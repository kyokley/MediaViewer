import logging
import uuid

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from mediaviewer import b2
from mediaviewer.models import MediaFile, MediaPath
from mediaviewer.models.mediapath import B2_URI_PREFIX

logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = {
    ".avi",
    ".flv",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".mpg",
    ".mpeg",
    ".ts",
    ".webm",
    ".wmv",
}


class Command(BaseCommand):
    help = (
        "Upload media files from local storage to a Backblaze B2 bucket and "
        "update the corresponding MediaPath records to point at B2."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--bucket",
            default=None,
            help="Bucket name (default: settings.B2_BUCKET_NAME)",
        )
        parser.add_argument(
            "--prefix",
            default=None,
            help="Base name prefix (default: settings.B2_NAME_PREFIX)",
        )
        parser.add_argument(
            "--delete-local",
            action="store_true",
            help="Delete local files after they have been uploaded successfully",
        )
        parser.add_argument(
            "--media-path",
            type=int,
            default=None,
            help="Only upload the MediaPath with the given pk",
        )

    def handle(self, *args, **options):
        bucket = options["bucket"] or settings.B2_BUCKET_NAME
        if not bucket:
            raise CommandError(
                "No bucket specified. Pass --bucket or set B2_BUCKET_NAME."
            )

        prefix = (
            options["prefix"]
            if options["prefix"] is not None
            else settings.B2_NAME_PREFIX
        )
        if prefix and not prefix.endswith("/"):
            prefix = f"{prefix}/"

        qs = MediaPath.objects.exclude(_path__startswith=B2_URI_PREFIX).filter(
            skip=False
        )
        if options["media_path"]:
            qs = qs.filter(pk=options["media_path"])
            if not qs.exists():
                logger.warning(
                    "MediaPath %s not found or already on B2; nothing to do",
                    options["media_path"],
                )
                return

        client = b2.get_b2_client()
        for mp in qs:
            self._upload_media_path(client, mp, bucket, prefix, options["delete_local"])

    def _upload_media_path(self, client, mp, bucket, prefix, delete_local):
        if not mp._path:
            logger.warning("MediaPath %s has no path; skipping", mp)
            return
        if mp.tv:
            videos = [
                (mf, mf.filename, mp.path / mf.filename, mf.subtitle_files or [])
                for mf in mp.mediafile_set.filter(hide=False)
            ]
        elif mp.movie:
            video_file = self._find_video_file(mp.path)
            if video_file is None:
                logger.warning("No video file found in %s; skipping", mp.path)
                return
            videos = [(None, video_file.name, video_file, mp.subtitle_files or [])]
        else:
            logger.warning("MediaPath %s has no tv or movie; skipping", mp)
            return

        key_prefix = f"{prefix}{mp.pk}/"
        logical_key_prefix = f"{key_prefix}{mp.path.name}/"
        missing_videos = [
            local_path for _, _, local_path, _ in videos if not local_path.exists()
        ]
        if missing_videos:
            logger.warning(
                "Missing video files for MediaPath %s; skipping upload: %s",
                mp,
                missing_videos,
            )
            return
        uploaded = []
        for media_file, filename, local_path, subtitles in videos:
            object_uuid = uuid.uuid4()
            key = f"{key_prefix}{object_uuid}{local_path.suffix}"
            client.upload_file(local_path, bucket, key)
            subtitle_uploads = []
            for subtitle in subtitles:
                subtitle_path = mp.path / subtitle
                if not subtitle_path.exists():
                    raise CommandError(f"Subtitle file {subtitle_path} does not exist")
                subtitle_uuid = uuid.uuid4()
                client.upload_file(
                    subtitle_path, bucket, f"{key_prefix}{subtitle_uuid}.vtt"
                )
                subtitle_uploads.append((subtitle, subtitle_path, subtitle_uuid))
            uploaded.append(
                (media_file, filename, local_path, object_uuid, subtitle_uploads)
            )

        if not uploaded:
            logger.warning("Nothing uploaded for MediaPath %s", mp)
            return

        with transaction.atomic():
            mp._path = f"b2://{bucket}/{logical_key_prefix}"
            if mp.movie:
                mp.filename = uploaded[0][1]
                mp.subtitle_files = [
                    f"{subtitle_uuid}.vtt" for _, _, subtitle_uuid in uploaded[0][4]
                ]
            mp.save()

            for (
                media_file,
                filename,
                local_path,
                object_uuid,
                subtitle_uploads,
            ) in uploaded:
                if media_file is None:
                    media_file = MediaFile.objects.create(
                        media_path=mp, filename=filename
                    )
                media_file.b2_uuid = object_uuid
                media_file.size = local_path.stat().st_size
                media_file.subtitle_files = [
                    f"{subtitle_uuid}.vtt" for _, _, subtitle_uuid in subtitle_uploads
                ]
                media_file.save(
                    update_fields=("b2_uuid", "size", "subtitle_files", "date_edited")
                )

        if delete_local:
            for _, _, local_path, _, subtitles in uploaded:
                local_path.unlink()
                logger.info("Deleted %s", local_path)
                for _, subtitle_path, _ in subtitles:
                    subtitle_path.unlink()
                    logger.info("Deleted %s", subtitle_path)

    @staticmethod
    def _find_video_file(directory):
        if not directory or not directory.exists() or not directory.is_dir():
            return None
        candidates = [
            candidate
            for candidate in directory.iterdir()
            if candidate.is_file() and candidate.suffix.lower() in VIDEO_EXTENSIONS
        ]
        if not candidates:
            return None
        # Prefer the largest file: trailers/samples are usually smaller.
        return max(candidates, key=lambda p: p.stat().st_size)
