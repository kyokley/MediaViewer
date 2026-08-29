import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from mediaviewer import b2
from mediaviewer.models import MediaPath
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
            files = [
                (mf.filename, mp.path / mf.filename)
                for mf in mp.mediafile_set.filter(hide=False)
            ]
        elif mp.movie:
            video_file = self._find_video_file(mp.path)
            if video_file is None:
                logger.warning("No video file found in %s; skipping", mp.path)
                return
            files = [(video_file.name, video_file)]
        else:
            logger.warning("MediaPath %s has no tv or movie; skipping", mp)
            return

        # Include the pk so MediaPaths sharing a directory basename cannot
        # collide on the same B2 name prefix.
        key_prefix = f"{prefix}{mp.pk}/{mp.path.name}/"
        uploaded = []
        for filename, local_path in files:
            if not local_path.exists():
                logger.warning("File %s does not exist; skipping", local_path)
                continue
            key = f"{key_prefix}{filename}"
            client.upload_file(local_path, bucket, key)
            uploaded.append((filename, local_path))

        if not uploaded:
            logger.warning("Nothing uploaded for MediaPath %s", mp)
            return

        mp._path = f"b2://{bucket}/{key_prefix}"
        if mp.movie:
            mp.filename = uploaded[0][0]
        mp.save()

        if delete_local:
            for _, local_path in uploaded:
                local_path.unlink()
                logger.info("Deleted %s", local_path)

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
