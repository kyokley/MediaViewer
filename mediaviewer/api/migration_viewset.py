import copy
import json
import re
import uuid
from pathlib import PurePath

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.core import signing
from django.db import IntegrityError, models, transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from mediaviewer.models import MediaFile, MediaPath, MigrationOwnership

MAX_CANDIDATES = 1000
SNAPSHOT_SALT = "mediaviewer.migration.snapshot.v1"
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


class MigrationViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAdminUser,)

    @action(detail=False, methods=["get", "post", "delete"], url_path="run")
    def run(self, request):
        if request.method == "GET":
            lock = MigrationOwnership.objects.filter(pk=1).first()
            if lock is None:
                return Response({"run_id": None, "owner_id": None})
            return Response(
                {
                    "run_id": str(lock.run_id) if lock.run_id else None,
                    "owner_id": lock.owner_id,
                }
            )
        if request.method == "POST":
            try:
                run_id = uuid.UUID(str(request.data.get("run_id", "")))
            except (ValueError, TypeError, AttributeError):
                return Response(
                    {"error": "run_id must be a UUID"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if request.data.get("writers_paused") is not True:
                return Response(
                    {"error": "writers_paused must be true"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                lock, _ = MigrationOwnership.objects.get_or_create(pk=1)
                lock = MigrationOwnership.objects.select_for_update().get(pk=1)
                if lock.run_id and (
                    lock.run_id != run_id or lock.owner_id != request.user.pk
                ):
                    return Response(
                        {"error": "Another migration run owns the lock"},
                        status=status.HTTP_409_CONFLICT,
                    )
                lock.run_id, lock.owner = run_id, request.user
                lock.save(update_fields=("run_id", "owner"))
            return Response(
                {"acquired": True, "run_id": str(run_id), "owner_id": request.user.pk}
            )
        try:
            run_id = uuid.UUID(str(request.data.get("run_id", "")))
        except (ValueError, TypeError, AttributeError):
            return Response(
                {"error": "run_id must be a UUID"}, status=status.HTTP_400_BAD_REQUEST
            )
        with transaction.atomic():
            lock, _ = MigrationOwnership.objects.get_or_create(pk=1)
            lock = MigrationOwnership.objects.select_for_update().get(pk=1)
            if lock.run_id is None:
                return Response({"released": True})
            if lock.run_id != run_id or lock.owner_id != request.user.pk:
                return Response(
                    {"error": "Migration lock owner or run_id does not match"},
                    status=status.HTTP_409_CONFLICT,
                )
            lock.run_id, lock.owner = None, None
            lock.save(update_fields=("run_id", "owner"))
        return Response({"released": True})

    @action(detail=False, methods=["get"], url_path="candidates")
    def candidates(self, request):
        try:
            limit = int(request.query_params.get("limit", "100"))
            if limit < 1 or limit > MAX_CANDIDATES:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"error": f"limit must be between 1 and {MAX_CANDIDATES}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        rows = []
        qs = (
            MediaPath.objects.filter(skip=False)
            .exclude(_path="")
            .exclude(_path__startswith="b2://")
            .filter(models.Q(tv__isnull=False) | models.Q(movie__isnull=False))
            .order_by("pk")[:limit]
        )
        for parent in qs:
            children = _children(parent)
            try:
                target = _target(
                    parent,
                    request.query_params.get("bucket"),
                    request.query_params.get("prefix"),
                )
            except (ValueError, TypeError):
                rows.append(
                    {
                        "pk": parent.pk,
                        "error": "Cannot derive upload target; configure a valid B2 bucket and relative prefix.",
                    }
                )
                continue
            payload = _snapshot_payload(parent, children, target)
            rows.append(
                {
                    "pk": parent.pk,
                    "path": parent._path,
                    "tv": parent.tv_id,
                    "movie": parent.movie_id,
                    "filename": parent.filename,
                    "subtitle_files": parent.subtitle_files,
                    "children": [
                        {
                            "pk": c.pk,
                            "filename": c.filename,
                            "b2_uuid": str(c.b2_uuid) if c.b2_uuid else None,
                            "size": c.size,
                            "subtitle_files": c.subtitle_files,
                        }
                        for c in children
                    ],
                    "snapshot": signing.dumps(
                        payload,
                        salt=SNAPSHOT_SALT,
                        serializer=SnapshotSerializer,
                        compress=True,
                    ),
                    "target": target,
                }
            )
        return Response({"version": 1, "candidates": rows})

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        try:
            run_id = uuid.UUID(str(request.data.get("run_id", "")))
            token = request.data["snapshot"]
            manifest = request.data["files"]
            if not isinstance(manifest, list):
                raise ValueError("files must be a list")
            signed_payload = signing.loads(
                token, salt=SNAPSHOT_SALT, serializer=SnapshotSerializer
            )
        except (KeyError, TypeError, ValueError, signing.BadSignature):
            return Response(
                {"error": "Invalid run_id, snapshot, or files manifest"},
                status=status.HTTP_400_BAD_REQUEST,
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
                        status=status.HTTP_409_CONFLICT,
                    )
                parent = get_object_or_404(MediaPath.objects.select_for_update(), pk=pk)
                children = list(
                    MediaFile.objects.select_for_update()
                    .filter(media_path_id=parent.pk)
                    .order_by("pk")
                )
                if not _eligible(parent):
                    return Response(
                        {"error": "Candidate is no longer eligible"},
                        status=status.HTTP_409_CONFLICT,
                    )
                # Target overrides are signed into the inventory token, so publish
                # does not need to resend (or trust) the query parameters.
                target = (
                    signed_payload.get("target")
                    if isinstance(signed_payload, dict)
                    else None
                )
                if not isinstance(target, dict):
                    return Response(
                        {"error": "Candidate snapshot is invalid"},
                        status=status.HTTP_409_CONFLICT,
                    )
                if signed_payload != _snapshot_payload(parent, children, target):
                    return Response(
                        {"error": "Candidate snapshot is stale"},
                        status=status.HTTP_409_CONFLICT,
                    )
                if any(c.b2_uuid is not None for c in children):
                    return Response(
                        {"error": "Candidate already contains B2 UUIDs"},
                        status=status.HTTP_409_CONFLICT,
                    )
                tv = bool(parent.tv_id)
                if tv and parent.filename not in (None, ""):
                    raise ValueError("TV parent cannot have a filename")
                if tv and parent.subtitle_files not in (None, []):
                    raise ValueError(
                        "TV parent subtitles must be null or an empty list"
                    )
                expected_ids = {c.pk for c in children}
                seen = set()
                proposed_uuids = set()
                validated = []
                for entry in manifest:
                    if not isinstance(entry, dict):
                        raise ValueError("Each files entry must be an object")
                    if set(entry) != {
                        "pk",
                        "filename",
                        "b2_uuid",
                        "size",
                        "subtitle_files",
                    }:
                        raise ValueError(
                            "Each files entry must contain exactly pk, filename, b2_uuid, size, and subtitle_files"
                        )
                    child_id = entry.get("pk")
                    if child_id is not None and (
                        isinstance(child_id, bool)
                        or not isinstance(child_id, int)
                        or child_id not in expected_ids
                    ):
                        raise ValueError("Manifest contains an unknown child pk")
                    if child_id is not None and child_id in seen:
                        raise ValueError("Manifest contains duplicate child pks")
                    if child_id is not None:
                        seen.add(child_id)
                    filename = entry.get("filename")
                    if (
                        not isinstance(filename, str)
                        or not filename
                        or "\\" in filename
                        or PurePath(filename).name != filename
                        or filename in (".", "..")
                        or PurePath(filename).suffix.lower() not in VIDEO_EXTENSIONS
                    ):
                        raise ValueError(
                            "filename must be a direct-child video filename"
                        )
                    if child_id is not None and filename != next(
                        c.filename for c in children if c.pk == child_id
                    ):
                        raise ValueError(
                            "filename must match the existing child record"
                        )
                    try:
                        object_uuid = uuid.UUID(str(entry.get("b2_uuid")))
                    except (ValueError, TypeError, AttributeError):
                        raise ValueError("b2_uuid must be a UUID")
                    if (
                        object_uuid.int == 0
                        or object_uuid in proposed_uuids
                        or MediaFile.objects.filter(b2_uuid=object_uuid).exists()
                    ):
                        raise ValueError("b2_uuid must be nonzero and unique")
                    proposed_uuids.add(object_uuid)
                    size = entry.get("size")
                    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
                        raise ValueError("size must be a positive integer")
                    subtitles = _subtitle_list(entry["subtitle_files"])
                    validated.append((child_id, filename, object_uuid, size, subtitles))
                if tv:
                    if (
                        not expected_ids
                        or not validated
                        or seen != expected_ids
                        or any(child_id is None for child_id, *_ in validated)
                    ):
                        raise ValueError(
                            "TV manifest must include every existing child exactly once"
                        )
                else:
                    if (
                        len(validated) != 1
                        or (expected_ids and (seen != expected_ids or None in seen))
                        or (not expected_ids and validated[0][0] is not None)
                    ):
                        raise ValueError(
                            "Movie manifest must cover its one existing child or one new child"
                        )
                    if (
                        parent.filename not in (None, "")
                        and validated[0][1] != parent.filename
                    ):
                        raise ValueError(
                            "Movie filename must match the existing parent filename"
                        )
                by_id = {c.pk: c for c in children}
                for child_id, filename, object_uuid, size, subtitles in validated:
                    if child_id is None:
                        child = MediaFile(media_path=parent, filename=filename)
                        child.b2_uuid, child.size, child.subtitle_files = (
                            object_uuid,
                            size,
                            subtitles,
                        )
                        child.save()
                    else:
                        child = by_id[child_id]
                        child.b2_uuid, child.size, child.subtitle_files = (
                            object_uuid,
                            size,
                            subtitles,
                        )
                        child.save(update_fields=("b2_uuid", "size", "subtitle_files"))
                parent._path = target["path"]
                if not tv:
                    parent.filename = validated[0][1]
                    parent.subtitle_files = validated[0][4]
                parent.save(
                    update_fields=("_path", "filename", "subtitle_files", "date_edited")
                )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response(
                {"error": "Manifest violates a media UUID constraint"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"pk": parent.pk, "path": parent._path, "published": True})
