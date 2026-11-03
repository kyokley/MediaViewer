import hashlib
import re
import unicodedata
from pathlib import Path

from mediaviewer.models import MediaFile, VideoProgress


def media_content_disposition(obj, filename):
    media_path = obj.media_path
    tv = getattr(media_path, "tv", None)
    if tv:
        title = tv.name
        season = getattr(obj, "season", None)
        episode = getattr(obj, "episode", None)
    else:
        movie = getattr(media_path, "movie", None)
        title = getattr(movie, "name", None) or getattr(obj, "name", None)
        season = episode = None

    ascii_title = (
        unicodedata.normalize("NFKD", title or "").encode("ascii", "ignore").decode()
    )
    safe_title = re.sub(r'[\\/:*?"<>|\x00-\x1f\x7f]+', ".", ascii_title)
    safe_title = re.sub(r"\s+", ".", safe_title)
    safe_title = re.sub(r"\.+", ".", safe_title).strip(".") or "video"
    episode_name = (
        f".S{season:02d}E{episode:02d}"
        if season is not None and episode is not None
        else ""
    )
    suffix = Path(filename).suffix
    if not suffix or not re.fullmatch(r"\.[A-Za-z0-9._-]+", suffix):
        suffix = ""
    return f'inline; filename="{safe_title}{episode_name}{suffix}"'


def b2_media_path(obj):
    if isinstance(obj, MediaFile):
        media_path = obj.media_path
    else:
        media_path = obj.mediapath_set.order_by("-pk").first()
    return media_path if media_path and media_path.is_b2 else None


def has_b2_source(obj, media_path):
    if isinstance(obj, MediaFile):
        return bool(obj.filename)

    filename = media_path.filename
    if not filename:
        return False
    uuid_files = media_path.mediafile_set.filter(
        filename=filename, b2_uuid__isnull=False
    )
    return uuid_files.count() <= 1


def progress_identifier(token, obj, media_path):
    existing_progress = (
        VideoProgress.objects.filter(
            user=token.user, media_file=token.media_file, movie=token.movie
        )
        .order_by("-date_edited")
        .first()
    )
    if existing_progress:
        return existing_progress.hashed_filename

    if isinstance(obj, MediaFile):
        media_identity = f"mediafile:{obj.pk}"
        logical_filename = obj.filename
    else:
        media_identity = f"movie:{obj.pk}"
        logical_filename = media_path.filename
    logical_identity = f"b2:{media_path.pk}:{media_identity}:{logical_filename}"
    return hashlib.sha256(logical_identity.encode("utf-8")).hexdigest()
