import re
from pathlib import Path

from django.conf import settings
from django.db import models


class FilenameScrapeFormat(models.Model):
    nameRegex = models.TextField(
        db_column="nameregex",
        blank=True,
        null=True,
    )
    seasonRegex = models.TextField(db_column="seasonregex", blank=True, null=True)
    episodeRegex = models.TextField(db_column="episoderegex", blank=True, null=True)
    subPeriods = models.BooleanField(db_column="subperiods", blank=True, null=False)
    useSearchTerm = models.BooleanField(
        db_column="usesearchterm", blank=True, null=False
    )

    class Meta:
        app_label = "mediaviewer"
        db_table = "filenamescrapeformat"

    def __str__(self):
        return "id: %s n: %s s: %s e: %s subPeriods: %s useSearchTerm: %s" % (
            self.id,
            self.nameRegex,
            self.seasonRegex,
            self.episodeRegex,
            self.subPeriods,
            self.useSearchTerm,
        )

    @classmethod
    def new(
        cls, nameRegex, seasonRegex, episodeRegex, subPeriods=False, useSearchTerm=False
    ):
        obj = cls()
        obj.nameRegex = nameRegex
        obj.seasonRegex = seasonRegex
        obj.episodeRegex = episodeRegex
        obj.subPeriods = subPeriods
        obj.useSearchTerm = useSearchTerm
        obj.save()
        return obj

    def valid_for_filename(self, filename):
        from mediaviewer.models import TV

        tv = None

        if self.subPeriods:
            filename = filename.replace(".", " ")

        name = re.findall(self.nameRegex, filename)
        name = name[0].strip() if name and len(name[0]) > 1 else None

        if not name:
            return None
        else:
            query = models.Q()
            words = name.split()
            for word in words:
                query = query | models.Q(name__icontains=word)
            tv_objs = TV.objects.filter(query).order_by("-pk")
            max_word_score = 0

            for tv_obj in tv_objs:
                word_score = self._tv_name_score_for_words(tv_obj, words)
                if word_score > max_word_score:
                    tv = tv_obj
                    max_word_score = word_score

            if not tv:
                return None

        season = re.findall(self.seasonRegex, filename)
        if not season or not season[0].strip():
            return None
        else:
            season = season[0]

            if not season.isdigit() or int(season) == 0:
                return None

        episode = re.findall(self.episodeRegex, filename)
        if not episode or not episode[0].strip():
            return None
        else:
            episode = episode[0]

            if not episode.isdigit() or int(episode) == 0:
                return None

        # Filenames containing 264 are most likely not right
        if int(season) == 2 and int(episode) in (64, 65):
            return None

        return (tv, name, season, episode)

    @staticmethod
    def _tv_name_score_for_words(tv, words):
        count = 0
        for word in words:
            if word.lower() in tv.name.lower():
                count += 1

        if tv.name.lower() == " ".join([x.lower() for x in words]):
            count += 5
        return count

    @classmethod
    def tv_for_filename(cls, filename):
        from mediaviewer.models import MediaPath, TV
        from mediaviewer.thetvdb import parse_tv_filename, resolve_series_name

        parsed = parse_tv_filename(filename)
        if parsed is None:
            parsed = cls._parse_configured_filename(filename)
        if parsed is None:
            return None

        title, season, episode = parsed
        if (
            not isinstance(title, str)
            or not title.strip()
            or type(season) is not int
            or season < 0
            or type(episode) is not int
            or episode <= 0
        ):
            return None

        series_name = resolve_series_name(title)
        if not isinstance(series_name, str) or not series_name.strip():
            return None

        matching_tvs = list(TV.objects.filter(name__iexact=series_name.strip())[:2])
        if not matching_tvs:
            tv = TV.objects.create(name=series_name.strip())
        else:
            tv = matching_tvs[0]

        media_paths = tv.mediapath_set.order_by("-pk")
        current_path = media_paths.first()
        if current_path is not None and current_path.is_b2:
            return current_path

        existing_b2_path = media_paths.filter(_path__startswith="b2://").first()
        if existing_b2_path is not None:
            return existing_b2_path

        bucket = getattr(settings, "B2_BUCKET_NAME", "")
        prefix = getattr(settings, "B2_NAME_PREFIX", "")
        if (
            not isinstance(bucket, str)
            or not bucket.strip()
            or "/" in bucket
            or "\\" in bucket
            or bucket != bucket.strip()
            or not isinstance(prefix, str)
            or any(ord(character) < 32 for character in prefix)
        ):
            return None

        try:
            directory_name = Path(current_path._path).name if current_path else ""
        except (TypeError, ValueError, OSError):
            return None
        if not directory_name:
            directory_name = tv.name
        if (
            not isinstance(directory_name, str)
            or not directory_name.strip()
            or directory_name in (".", "..")
            or "/" in directory_name
            or "\\" in directory_name
            or any(ord(character) < 32 for character in directory_name)
        ):
            return None

        uri = f"b2://{bucket}/{prefix}{directory_name}/"
        if len(uri) > MediaPath._meta.get_field("_path").max_length:
            return None

        media_path, _ = MediaPath.objects.get_or_create(
            _path=uri, defaults={"tv": tv}
        )
        if media_path.tv_id != tv.pk or media_path.movie_id is not None:
            return None
        return media_path

    @classmethod
    def _parse_configured_filename(cls, filename):
        if not isinstance(filename, str) or not filename.strip():
            return None

        for scraper in cls.objects.all():
            candidate = filename.replace(".", " ") if scraper.subPeriods else filename
            try:
                name_matches = re.findall(scraper.nameRegex or "", candidate)
                season_matches = re.findall(scraper.seasonRegex or "", candidate)
                episode_matches = re.findall(scraper.episodeRegex or "", candidate)
            except re.error:
                continue

            if not name_matches or not season_matches or not episode_matches:
                continue
            name = cls._first_regex_value(name_matches[0])
            season = cls._first_regex_value(season_matches[0])
            episode = cls._first_regex_value(episode_matches[0])
            if not isinstance(name, str) or len(name.strip()) <= 1:
                continue
            if (
                not isinstance(season, str)
                or not season.strip().isdigit()
                or not isinstance(episode, str)
                or not episode.strip().isdigit()
            ):
                continue
            season_number = int(season.strip())
            episode_number = int(episode.strip())
            if season_number < 0 or episode_number <= 0:
                continue
            return name.strip(), season_number, episode_number
        return None

    @staticmethod
    def _first_regex_value(value):
        if isinstance(value, tuple):
            return next((part for part in value if part), "")
        return value
