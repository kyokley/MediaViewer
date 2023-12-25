import re

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
            tv = TV.objects.filter(name__icontains=name).order_by("-pk").first()
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
