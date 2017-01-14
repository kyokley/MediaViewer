import time
from django.db import models
from mediaviewer.models.file import File
from mediaviewer.models.posterfile import PosterFile
from mediaviewer.models.usercomment import UserComment
from mediaviewer.models.tvdbconfiguration import (getDataFromIMDBByPath,
                                                  saveImageToDisk,
                                                  assignDataToPoster,
                                                  searchTVDBByName,
                                                  tvdbConfig,
                                                  )
from mediaviewer.models.mediagenre import MediaGenre
from datetime import datetime as dateObj
from datetime import timedelta
from django.utils.timezone import utc

from mediaviewer.log import log

class Path(models.Model):
    localpathstr = models.TextField(blank=True)
    remotepathstr = models.TextField(blank=True)
    skip = models.BooleanField(blank=True)
    is_movie = models.BooleanField(blank=False, null=False, db_column='ismovie')
    defaultScraper = models.ForeignKey('mediaviewer.FilenameScrapeFormat', null=True, blank=True, db_column='defaultscraperid')
    tvdb_id = models.TextField(null=True, blank=True)
    server = models.TextField(blank=False, null=False)
    defaultsearchstr = models.TextField(null=True, blank=True)
    imdb_id = models.TextField(null=True, blank=True)
    override_display_name = models.TextField(null=True, blank=True, db_column='display_name')
    lastCreatedFileDate = models.DateTimeField(null=True, blank=True, db_column='lastcreatedfiledate')

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'path'

    def files(self):
        return File.objects.filter(path__localpathstr=self.localpathstr).filter(hide=False)

    @property
    def shortName(self):
        return self.localPath.rpartition('/')[-1]

    @property
    def localPath(self):
        return self.localpathstr

    localpath = localPath

    @property
    def remotePath(self):
        return self.remotepathstr

    remotepath = remotePath

    def displayName(self):
        return self.override_display_name or self.shortName.replace('.', ' ').title()

    def __unicode__(self):
        return 'id: %s r: %s l: %s' % (self.id, self.remotePath, self.localPath)

    def lastCreatedFileDateForSpan(self):
        last_date = self.lastCreatedFileDate
        return last_date and last_date.date().isoformat()

    @classmethod
    def distinctShowFolders(cls):
        refFiles = File.objects.filter(path__is_movie=False).order_by('path').distinct('path').select_related('path')
        paths = set([file.path for file in refFiles])
        pathDict = dict()
        for path in paths:
            lastDate = path.lastCreatedFileDate
            if path.shortName in pathDict:
                if lastDate and pathDict[path.shortName].lastCreatedFileDate < lastDate:
                    pathDict[path.shortName] = path
            else:
                pathDict[path.shortName] = path
        return pathDict

    def isMovie(self):
        return self.is_movie

    def isTVShow(self):
        return not self.isMovie()

    def _downloadPosterData(self, poster):
        try:
            if self.isMovie():
                log.debug('Path is for movies. Skipping.')
                return None
            else:
                poster.path = self

            imdbFailure = False
            data = getDataFromIMDBByPath(self, useExtendedPlot=False)
            try:
                if not data or ('Response' in data and data['Response'] == 'False'):
                    imdbFailure = True
            except Exception, e:
                log.error(e)
                log.error('Got unexpected data: %s' % data)
                imdbFailure = True

            if not imdbFailure:
                log.info('Using IMDB data')
                self._handleDataFromIMDB(data, poster)
            else:
                log.info('IMDB failed. Attempting to use TVDB.')
                self._handleDataFromTVDB(poster)
        except Exception, e:
            log.error(str(e), exc_info=True)
            assignDataToPoster({}, poster, foundNone=True)
        poster.save()
        return poster

    def _handleDataFromTVDB(self, poster):
        tvinfo = searchTVDBByName(self.defaultsearchstr or self.displayName())
        if tvinfo and tvinfo.get('results'):
            self.tvdb_id = tvinfo['results'][0]['id']
            result = tvinfo['results'][0]
            poster_path = result.get('poster_path')
            if poster_path:
                imgName = poster_path.rpartition('/')[-1]
                posterURL = '%s/%s/%s' % (tvdbConfig.url, tvdbConfig.still_size, imgName)
                saveImageToDisk(posterURL, imgName)
                poster.image = imgName
            assignDataToPoster(result, poster, foundNone=False)
        else:
            assignDataToPoster({}, poster, foundNone=True)

    def _handleDataFromIMDB(self, data, poster):
        imgName = data['Poster'].rpartition('/')[-1]
        saveImageToDisk(data['Poster'], imgName)
        poster.image = imgName

        assignDataToPoster(data, poster)

        data = getDataFromIMDBByPath(self, useExtendedPlot=True)
        assignDataToPoster(data, poster, onlyExtendedPlot=True)

    def _posterfileget(self):
        posterfile = PosterFile.objects.filter(path=self).first()

        if not posterfile:
            log.info('PosterFile not found. Creating a new one')
            poster = PosterFile()
            poster.datecreated = dateObj.utcnow().replace(tzinfo=utc)
            poster.dateedited = dateObj.utcnow().replace(tzinfo=utc)
            poster.path = self

            posterfile = self._downloadPosterData(poster)

        return posterfile
    def _posterfileset(self, val):
        val.path = self
        val.save()
    posterfile = property(fset=_posterfileset, fget=_posterfileget)

    def destroy(self):
        files = File.objects.filter(path=self)
        for file in files:
            file.delete()
        self.delete()

    def unwatched_tv_shows_since_date(self, user, daysBack=30):
        if self.isMovie():
            raise Exception('This function does not apply to movies')

        if daysBack > 0:
            refDate = dateObj.utcnow().replace(tzinfo=utc) - timedelta(days=daysBack)
            files = (File.objects.filter(path__localpathstr=self.localpathstr)
                                 .filter(datecreated__gt=refDate)
                                 .filter(hide=False)
                                 .all())
        else:
            files = (File.objects.filter(path__localpathstr=self.localpathstr)
                                 .filter(hide=False)
                                 .all())
        unwatched_files = set()
        for file in files:
            comment = file.usercomment(user)
            if not comment or not comment.viewed:
                unwatched_files.add(file)

        return unwatched_files

    def number_of_unwatched_shows_since_date(self, user, daysBack=30):
        return len(self.unwatched_tv_shows_since_date(user, daysBack=daysBack))

    def number_of_unwatched_shows(self, user):
        if not user:
            return 0

        files = (File.objects.filter(path__localpathstr=self.localpathstr)
                             .filter(hide=False))
        file_count = files.count()
        usercomments_count = (UserComment.objects.filter(user=user)
                                                 .filter(file__in=files)
                                                 .filter(viewed=True)
                                                 .count())
        return file_count - usercomments_count

    def populate_genres(self):
        if self.isMovie():
            raise ValueError('This function should not be applied to movie paths')

        posterfile = PosterFile.objects.filter(path=self).first()

        if not posterfile:
            # Try not to hammer the movieDBs so we'll add a small sleep
            time.sleep(.5)

        genres = (self.posterfile.genre
                    if self.posterfile.genre != 'Genre not found'
                    else None)

        if genres:
            split_genres = genres.split(', ')
            for genre in split_genres:
                MediaGenre.new(genre, path=self)
            return split_genres

    @classmethod
    def populate_all_genres(cls):
        all_paths = cls.objects.filter(is_movie=False).filter(hide=False)
        for path in all_paths:
            print(path.displayName(), path.populate_genres())
