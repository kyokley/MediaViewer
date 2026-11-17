import copy
import json
import re
import uuid
from pathlib import PurePath

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.core import signing
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response

from mediaviewer.models import MediaFile, MediaPath, MigrationOwnership

MAX_CANDIDATES = 1000
SNAPSHOT_SALT = "mediaviewer.migration.snapshot.v1"
FILE_CURSOR_SALT = "mediaviewer.file-cursor.v2"
VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".m4v",
    ".wmv",
    ".webm",
    ".mpeg",
    ".mpg",
    ".mpe",
    ".mpv",
    ".m2v",
    ".ts",
    ".m2ts",
    ".mts",
    ".3gp",
    ".flv",
    ".ogv",
    ".vob",
    ".divx",
    ".f4v",
    ".mxf",
}
UUID_FILENAME = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\.vtt$"
)


class SnapshotSerializer(signing.JSONSerializer):
    def dumps(self, obj):
        return json.dumps(
            obj, cls=DjangoJSONEncoder, sort_keys=True, separators=(",", ":")
        ).encode("latin-1")

    def loads(self, data):
        return json.loads(data.decode("latin-1"))


def _eligible(parent):
    return (
        not parent.skip
        and bool(parent._path)
        and not parent.is_b2
        and (bool(parent.tv_id) ^ bool(parent.movie_id))
    )


def _current_movie_path(parent):
    return not parent.movie_id or (
        parent.movie.mediapath_set.order_by("-pk").values_list("pk", flat=True).first()
        == parent.pk
    )


def _file_snapshot(parent, child):
    result = {
        "parent": _parent_state(parent),
        "child": _child_state(child) if child else None,
    }
    if parent.movie_id:
        result["movie_children"] = [_child_state(item) for item in _children(parent)]
    return result


def _target_data(target):
    if not target.is_b2:
        raise ValueError("Reserved target path is not a B2 URI")
    staged = copy.copy(target)
    return {
        "bucket": target.bucket,
        "path": target._path,
        "b2_upload_prefix": staged.b2_upload_prefix,
    }


def _valid_video_filename(filename):
    return (
        isinstance(filename, str)
        and bool(filename)
        and len(filename) <= MediaFile._meta.get_field("filename").max_length
        and "\x00" not in filename
        and "/" not in filename
        and "\\" not in filename
        and PurePath(filename).name == filename
        and filename not in (".", "..")
        and PurePath(filename).suffix.lower() in VIDEO_EXTENSIONS
    )


def _reservation_unchanged(target, expected, source):
    current = _model_state(target)
    if not isinstance(expected, dict) or current.keys() != expected.keys():
        return False
    for key, value in expected.items():
        if key == "tv_id" and source.tv_id and value is None:
            if current[key] not in (None, source.tv_id):
                return False
        elif current[key] != value:
            return False
    return current.get("movie_id") is None


def _replayed_child_matches(child, prepared, source, target):
    file = prepared["file"]
    original = prepared["snapshot"].get("child")
    if original is None:
        expected = {
            "filename": file["filename"],
            "display_name": "",
            "season": None,
            "episode": None,
            "scraper_id": None,
            "_poster_id": None,
            "hide": False,
        }
    else:
        expected = dict(original)
    expected.update(
        {
            "media_path_id": target.pk if source.tv_id else source.pk,
            "b2_uuid": str(uuid.UUID(file["b2_uuid"])),
            "size": file["size"],
            "subtitle_files": [sub["filename"] for sub in file["subtitles"]],
        }
    )
    current = _model_state(child)
    return all(
        current.get(key) == value
        for key, value in expected.items()
        if key != "date_edited"
    )


def _replayed_movie_parent_matches(source, prepared):
    expected = dict(prepared["snapshot"]["parent"])
    file = prepared["file"]
    expected.update(
        {
            "_path": prepared["target_path"],
            "filename": file["filename"],
            "subtitle_files": [sub["filename"] for sub in file["subtitles"]],
        }
    )
    current = _model_state(source)
    return all(
        current.get(key) == value
        for key, value in expected.items()
        if key != "date_edited"
    )


def _children(parent):
    return list(MediaFile.objects.filter(media_path_id=parent.pk).order_by("pk"))


def _target(parent, bucket, prefix):
    bucket = bucket or getattr(settings, "B2_BUCKET_NAME", "")
    prefix = prefix if prefix is not None else getattr(settings, "B2_NAME_PREFIX", "")
    if not isinstance(bucket, str) or not bucket.strip():
        raise ValueError("Set B2_BUCKET_NAME or provide a bucket query parameter")
    if (
        not isinstance(prefix, str)
        or prefix.startswith("/")
        or ".." in prefix.split("/")
    ):
        raise ValueError("Provide a relative B2 prefix without '..' path segments")
    normalized_prefix = prefix.strip("/")
    directory = PurePath(str(parent._path).rstrip("/\\")).name
    if not directory:
        raise ValueError("Source path must include a directory name")
    key = (
        "/".join(
            part for part in (normalized_prefix, str(parent.pk), directory) if part
        )
        + "/"
    )
    staged = copy.copy(parent)
    staged._path = f"b2://{bucket}/{key}"
    return {
        "bucket": bucket,
        "path": staged._path,
        "b2_upload_prefix": staged.b2_upload_prefix,
    }


def _parent_state(parent):
    return _model_state(parent)


def _child_state(child):
    return _model_state(child)


def _model_state(instance):
    state = {}
    for field in instance._meta.concrete_fields:
        value = getattr(instance, field.attname)
        state[field.attname] = json.loads(json.dumps(value, cls=DjangoJSONEncoder))
    return state


def _snapshot_payload(parent, children, target):
    return {
        "parent": _parent_state(parent),
        "children": [_child_state(c) for c in children],
        "target": target,
    }


def _subtitle_list(value):
    if not isinstance(value, list) or any(
        not isinstance(x, str) or not UUID_FILENAME.fullmatch(x) for x in value
    ):
        raise ValueError("subtitle_files must contain UUID.vtt filenames")
    if len(value) != len(set(value)):
        raise ValueError("subtitle_files cannot contain duplicates")
    return value


class FileMigrationMixin:
    permission_classes = ()

    @action(detail=False, methods=["get"], url_path="remaining-files")
    def remaining_files(self, request):
        remaining = MediaFile.objects.filter(b2_uuid__isnull=True).count()
        return Response({"version": 1, "remaining_mediafiles": remaining})

    @action(detail=False, methods=["get"], url_path="file-candidates")
    def file_candidates(self, request):
        try:
            limit = int(request.query_params.get("limit", "100"))
            if not 1 <= limit <= MAX_CANDIDATES:
                raise ValueError
            cursor = request.query_params.get("cursor")
            after = after_child = None
            if cursor:
                decoded = signing.loads(cursor, salt=FILE_CURSOR_SALT)
                after, after_child = decoded["after"], decoded["child"]
                if any(
                    isinstance(v, bool) or not isinstance(v, int) or v < 0
                    for v in (after, after_child)
                ):
                    raise ValueError
        except (TypeError, ValueError, signing.BadSignature, KeyError):
            return Response({"error": "Invalid limit or cursor"}, status=400)
        candidates = []
        last = (after, after_child) if cursor else None
        parents = MediaPath.objects.all()
        if after is not None:
            parents = parents.filter(pk__lte=after)
        parents = parents.order_by("-pk")
        for parent in parents.iterator():
            if not _eligible(parent):
                continue
            if not _current_movie_path(parent):
                continue
            children = _children(parent)
            if parent.tv_id:
                rows = [
                    (child, "tv")
                    for child in reversed(children)
                    if child.b2_uuid is None
                ]
            else:
                if len(children) > 1:
                    return Response(
                        {
                            "error": f"Movie source {parent.pk} has ambiguous file membership"
                        },
                        status=409,
                    )
                if any(child.b2_uuid is not None for child in children):
                    continue
                rows = [(children[0] if children else None, "movie")]
            for child, kind in rows:
                payload = _file_snapshot(parent, child)
                candidates.append(
                    {
                        "source_pk": parent.pk,
                        "mediafile_pk": child.pk if child else None,
                        "kind": kind,
                        "path": parent._path,
                        "filename": child.filename if child else parent.filename,
                        "snapshot": signing.dumps(
                            payload, salt=SNAPSHOT_SALT, serializer=SnapshotSerializer
                        ),
                    }
                )
                candidate_key = (parent.pk, child.pk if child else 0)
                if last is not None and candidate_key >= last:
                    candidates.pop()
                    continue
                if len(candidates) == limit:
                    next_cursor = signing.dumps(
                        {"after": candidate_key[0], "child": candidate_key[1]},
                        salt=FILE_CURSOR_SALT,
                    )
                    return Response(
                        {
                            "version": 1,
                            "candidates": candidates,
                            "next_cursor": next_cursor,
                        }
                    )
        return Response({"version": 1, "candidates": candidates, "next_cursor": None})

    @action(detail=True, methods=["post"], url_path="prepare-file")
    def prepare_file(self, request, pk=None):
        try:
            run_id = uuid.UUID(str(request.data["run_id"]))
            snapshot = request.data["snapshot"]
            file = request.data["file"]
            if not isinstance(file, dict) or set(file) != {
                "pk",
                "filename",
                "b2_uuid",
                "size",
                "sha1",
                "subtitles",
            }:
                raise ValueError("Invalid file manifest")
            object_uuid = uuid.UUID(str(file["b2_uuid"]))
            if file["pk"] is not None and (
                isinstance(file["pk"], bool)
                or not isinstance(file["pk"], int)
                or file["pk"] <= 0
            ):
                raise ValueError("pk must be a positive integer or null")
            if not _valid_video_filename(file["filename"]):
                raise ValueError("Invalid direct-child video filename")
            size = file["size"]
            if (
                object_uuid.int == 0
                or isinstance(size, bool)
                or not isinstance(size, int)
                or size <= 0
            ):
                raise ValueError("Invalid file UUID or size")
            if not isinstance(file["sha1"], str) or not re.fullmatch(
                r"[0-9a-fA-F]{40}", file["sha1"]
            ):
                raise ValueError("sha1 must contain 40 hexadecimal characters")
            subtitles = file["subtitles"]
            if not isinstance(subtitles, list):
                raise ValueError("subtitles must be a list")
            sub_names = []
            for sub in subtitles:
                if not isinstance(sub, dict) or set(sub) != {
                    "filename",
                    "size",
                    "sha1",
                }:
                    raise ValueError("Invalid subtitle manifest")
                if not UUID_FILENAME.fullmatch(sub["filename"]):
                    raise ValueError("Subtitle filename must be UUID.vtt")
                if (
                    isinstance(sub["size"], bool)
                    or not isinstance(sub["size"], int)
                    or sub["size"] < 0
                ):
                    raise ValueError("Subtitle size must be nonnegative")
                if not isinstance(sub["sha1"], str) or not re.fullmatch(
                    r"[0-9a-fA-F]{40}", sub["sha1"]
                ):
                    raise ValueError(
                        "Subtitle sha1 must contain 40 hexadecimal characters"
                    )
                sub_names.append(sub["filename"])
            if len(sub_names) != len(set(sub_names)):
                raise ValueError("Duplicate subtitle filename")
            signed = signing.loads(
                snapshot, salt=SNAPSHOT_SALT, serializer=SnapshotSerializer
            )
        except (KeyError, TypeError, ValueError, signing.BadSignature):
            return Response(
                {"error": "Invalid run_id, snapshot, or file manifest"}, status=400
            )
        try:
            with transaction.atomic():
                lock = (
                    MigrationOwnership.objects.select_for_update().filter(pk=1).first()
                )
                if (
                    not lock
                    or lock.run_id != run_id
                    or lock.owner_id != request.user.pk
                ):
                    return Response(
                        {"error": "Migration ownership is stale or does not match"},
                        status=409,
                    )
                source = get_object_or_404(MediaPath.objects.select_for_update(), pk=pk)
                child = (
                    MediaFile.objects.select_for_update()
                    .filter(pk=file["pk"], media_path=source)
                    .first()
                    if file["pk"] is not None
                    else None
                )
                source_children = list(
                    MediaFile.objects.select_for_update()
                    .filter(media_path=source)
                    .order_by("pk")
                )
                current = _file_snapshot(source, child)
                if (
                    not _eligible(source)
                    or not _current_movie_path(source)
                    or current != signed
                ):
                    return Response(
                        {"error": "Candidate snapshot is stale"}, status=409
                    )
                tv = bool(source.tv_id)
                if (tv and child is None) or (not tv and len(source_children) > 1):
                    return Response({"error": "Source file is ambiguous"}, status=409)
                if file["pk"] is None and (
                    tv
                    or (
                        source.filename not in (None, "")
                        and source.filename != file["filename"]
                    )
                ):
                    return Response(
                        {"error": "New file is not valid for source"}, status=400
                    )
                if child and file["filename"] != child.filename:
                    return Response(
                        {"error": "Filename does not match source child"}, status=400
                    )
                if (
                    MediaFile.objects.filter(b2_uuid=object_uuid)
                    .exclude(pk=child.pk if child else None)
                    .exists()
                ):
                    return Response({"error": "b2_uuid is already in use"}, status=400)
                existing = MediaPath.objects.filter(migration_source=source).first()
                if not tv:
                    target = source
                elif existing:
                    target = existing
                    if (
                        target.tv_id not in (None, source.tv_id)
                        or target.movie_id is not None
                    ):
                        return Response(
                            {"error": "Reserved target is incompatible"}, status=409
                        )
                    try:
                        target_data = _target_data(target)
                    except ValueError:
                        return Response(
                            {"error": "Reserved target path is invalid"}, status=409
                        )
                else:
                    target_data = _target(source, None, None)
                    target = MediaPath.objects.create(
                        _path=target_data["path"],
                        tv=None,
                        movie=None,
                        migration_source=source,
                    )
                    # The reserved path owns its ID shard, not the local source's.
                    target_source = copy.copy(source)
                    target_source.pk = target.pk
                    target_data = _target(target_source, None, None)
                    target._path = target_data["path"]
                    target.save(update_fields=("_path",))
                if not tv:
                    target_data = _target(source, None, None)
                elif existing:
                    target_data = _target_data(target)
                upload_target = copy.copy(target)
                upload_target._path = target_data["path"]
                manifest = {
                    "file": file,
                    "snapshot": signed,
                    "target_pk": target.pk,
                    "target_path": target_data["path"],
                    "target_state": _model_state(target),
                    "source_pk": source.pk,
                    "child_pk": child.pk if child else None,
                    "run_id": str(run_id),
                    "owner_id": request.user.pk,
                }
                prepared = signing.dumps(
                    manifest,
                    salt="mediaviewer.file-prepare.v1",
                    serializer=SnapshotSerializer,
                    compress=True,
                )
                return Response(
                    {
                        "prepared": prepared,
                        "target_pk": target.pk,
                        "bucket": target_data["bucket"],
                        "b2_upload_prefix": upload_target.b2_upload_prefix,
                    }
                )
        except IntegrityError:
            return Response(
                {"error": "Reserved target path is already in use"}, status=409
            )
        except ValueError:
            return Response({"error": "File preparation failed validation"}, status=400)

    @action(detail=True, methods=["post"], url_path="publish-file")
    def publish_file(self, request, pk=None):
        try:
            run_id = uuid.UUID(str(request.data["run_id"]))
            prepared = signing.loads(
                request.data["prepared"],
                salt="mediaviewer.file-prepare.v1",
                serializer=SnapshotSerializer,
            )
        except (KeyError, TypeError, ValueError, signing.BadSignature):
            return Response({"error": "Invalid run_id or prepared token"}, status=400)
        try:
            source_id = int(pk)
        except (TypeError, ValueError):
            return Response({"error": "Invalid source route"}, status=400)
        if not isinstance(prepared, dict) or (
            prepared.get("source_pk") != source_id
            or prepared.get("run_id") != str(run_id)
            or prepared.get("owner_id") != request.user.pk
        ):
            return Response(
                {"error": "Prepared token does not match request"}, status=409
            )
        file = prepared["file"]
        try:
            with transaction.atomic():
                lock = (
                    MigrationOwnership.objects.select_for_update().filter(pk=1).first()
                )
                if (
                    not lock
                    or lock.run_id != run_id
                    or lock.owner_id != request.user.pk
                ):
                    return Response(
                        {"error": "Migration ownership is stale or does not match"},
                        status=409,
                    )
                source = get_object_or_404(
                    MediaPath.objects.select_for_update(), pk=source_id
                )
                target_qs = MediaPath.objects.select_for_update()
                target = get_object_or_404(
                    target_qs,
                    pk=prepared["target_pk"],
                    **({"migration_source": source} if source.tv_id else {}),
                )
                child = (
                    MediaFile.objects.select_for_update()
                    .filter(pk=prepared["child_pk"])
                    .first()
                    if prepared["child_pk"]
                    else MediaFile.objects.select_for_update()
                    .filter(media_path=source, b2_uuid=file["b2_uuid"])
                    .first()
                )
                source_children = list(
                    MediaFile.objects.select_for_update()
                    .filter(media_path=source)
                    .order_by("pk")
                )
                object_uuid = uuid.UUID(file["b2_uuid"])
                if source.tv_id and not _reservation_unchanged(
                    target, prepared.get("target_state"), source
                ):
                    return Response(
                        {"error": "Reserved target changed after preparation"},
                        status=409,
                    )
                # Exact replay succeeds before current-source CAS checks.
                already = (
                    child is not None
                    and _current_movie_path(source)
                    and child.media_path_id
                    == (target.pk if source.tv_id else source.pk)
                    and child.b2_uuid == object_uuid
                    and child.size == file["size"]
                    and child.subtitle_files
                    == [s["filename"] for s in file["subtitles"]]
                    and (
                        target._path == prepared["target_path"]
                        if source.tv_id
                        else source._path == prepared["target_path"]
                    )
                    and _replayed_child_matches(child, prepared, source, target)
                    and (
                        not source.tv_id
                        or _parent_state(source) == prepared["snapshot"].get("parent")
                    )
                    and (
                        source.tv_id
                        or (
                            _replayed_movie_parent_matches(source, prepared)
                            and list(
                                MediaFile.objects.filter(media_path=source)
                                .order_by("pk")
                                .values_list("pk", flat=True)
                            )
                            == [child.pk]
                        )
                    )
                )
                if already:
                    return Response(
                        {
                            "published": True,
                            "mediafile_pk": child.pk,
                            "media_path_pk": target.pk if source.tv_id else source.pk,
                        }
                    )
                if child is not None and child.media_path_id != source.pk:
                    return Response(
                        {"error": "Source changed after preparation"}, status=409
                    )
                if (
                    not _eligible(source)
                    or not _current_movie_path(source)
                    or _file_snapshot(source, child) != prepared.get("snapshot")
                    or len(source_children) > 1
                    and not source.tv_id
                ):
                    return Response(
                        {"error": "Source changed after preparation"}, status=409
                    )
                if (
                    MediaFile.objects.filter(b2_uuid=object_uuid)
                    .exclude(pk=child.pk if child else None)
                    .exists()
                ):
                    return Response({"error": "b2_uuid is already in use"}, status=409)
                subtitles = [s["filename"] for s in file["subtitles"]]
                if source.tv_id:
                    target._path = prepared["target_path"]
                    target.tv_id, target.movie_id = source.tv_id, None
                    target.save(update_fields=("_path", "tv", "movie"))
                    if child is None or target.movie_id:
                        return Response(
                            {"error": "Invalid TV child reservation"}, status=409
                        )
                    child.media_path = target
                    child.b2_uuid, child.size, child.subtitle_files = (
                        object_uuid,
                        file["size"],
                        subtitles,
                    )
                    child.save(
                        update_fields=(
                            "media_path",
                            "b2_uuid",
                            "size",
                            "subtitle_files",
                        )
                    )
                else:
                    if child is None:
                        child = MediaFile(media_path=source, filename=file["filename"])
                    child.b2_uuid, child.size, child.subtitle_files = (
                        object_uuid,
                        file["size"],
                        subtitles,
                    )
                    child.save()
                    source._path, source.filename, source.subtitle_files = (
                        prepared["target_path"],
                        file["filename"],
                        subtitles,
                    )
                    source.save(
                        update_fields=(
                            "_path",
                            "filename",
                            "subtitle_files",
                            "date_edited",
                        )
                    )
                return Response(
                    {
                        "published": True,
                        "mediafile_pk": child.pk,
                        "media_path_pk": target.pk if source.tv_id else source.pk,
                    }
                )
        except IntegrityError:
            return Response(
                {"error": "File publication violates a media constraint"}, status=409
            )
