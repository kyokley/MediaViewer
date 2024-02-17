import re

from django.db import models
from django.db.models.functions import Length


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
                word_score = self._tv_name_score_for_words(
                    tv_obj, words)
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
        if int(season) == 2 and int(episode) == 64:
            return None

        return (tv, name, season, episode)

    @staticmethod
    def _tv_name_score_for_words(tv, words):
        count = 0
        for word in words:
            if word.lower() in tv.name.lower():
                count += 1

        if tv.name.lower() == ' '.join([x.lower()
                                        for x in words]):
            count += 5
        return count

    @classmethod
    def tv_for_filename(cls, filename):
        paths = []

        for scraper in FilenameScrapeFormat.objects.all():
            path = scraper.valid_for_filename(filename)
            if path:
                paths.append(path)

        paths.sort(key=lambda x: len(x[1]), reverse=True)
        return paths[0][0] if paths else ''
