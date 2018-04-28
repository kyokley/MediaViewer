import re
from django.db import models

class FilenameScrapeFormat(models.Model):
    nameRegex = models.TextField(db_column='nameregex', blank=True, null=True)
    seasonRegex = models.TextField(db_column='seasonregex', blank=True, null=True)
    episodeRegex = models.TextField(db_column='episoderegex', blank=True, null=True)
    subPeriods = models.BooleanField(db_column='subperiods', blank=True, null=False)
    useSearchTerm = models.BooleanField(db_column='usesearchterm', blank=True, null=False)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'filenamescrapeformat'

    def __unicode__(self):
        return 'id: %s n: %s s: %s e: %s subPeriods: %s useSearchTerm: %s' % (self.id, self.nameRegex, self.seasonRegex, self.episodeRegex, self.subPeriods, self.useSearchTerm)

    @classmethod
    def new(cls,
            nameRegex,
            seasonRegex,
            episodeRegex,
            subPeriods=False,
            useSearchTerm=False):
        obj = cls()
        obj.nameRegex = nameRegex
        obj.seasonRegex = seasonRegex
        obj.episodeRegex = episodeRegex
        obj.subPeriods = subPeriods
        obj.useSearchTerm = useSearchTerm
        obj.save()
        return obj

    def valid_for_filename(self, filename):
        from mediaviewer.models.path import Path

        path = None

        if self.subPeriods:
            filename = filename.replace('.', ' ')

        name = re.findall(self.nameRegex, filename)

        if not name:
            return None
        else:
            name = name[0]

            for p in Path.objects.filter(is_movie=False).order_by('-id'):
                if name.strip().lower() in p.displayName().lower():
                    path = p
                    break
            else:
                return None

        season = re.findall(self.seasonRegex, filename)
        if not season:
            return None
        else:
            season = season[0]

            if not season.isdigit():
                return None

        episode = re.findall(self.episodeRegex, filename)
        if not episode:
            return None
        else:
            episode = episode[0]

            if not episode.isdigit():
                return None

        return path

    @classmethod
    def path_for_filename(cls, filename):
        paths = []

        for scraper in FilenameScrapeFormat.objects.all():
            path = scraper.valid_for_filename(filename)
            if path:
                paths.append(path)

        paths.sort(key=lambda x: x.id, reverse=True)
        return paths[0] if paths else None
