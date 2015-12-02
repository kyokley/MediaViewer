from django.db import models
from mediaviewer.models.file import File
from mediaviewer.models.posterfile import PosterFile
from mediaviewer.models.tvdbconfiguration import (getDataFromIMDBByPath,
                                                  saveImageToDisk,
                                                  assignDataToPoster,
                                                  searchTVDBByName,
                                                  tvdbConfig,
                                                  )
from datetime import datetime as dateObj
from django.utils.timezone import utc

from mediaviewer.log import log

MOVIE_PATH_ID = 57
MOVIE = 'Movies'

class Path(models.Model):
    localpathstr = models.TextField(blank=True)
    remotepathstr = models.TextField(blank=True)
    skip = models.IntegerField(null=True, blank=True)
    defaultScraper = models.ForeignKey('mediaviewer.FilenameScrapeFormat', null=True, blank=True, db_column='defaultscraperid')
    tvdb_id = models.TextField(null=True, blank=True)
    server = models.TextField(blank=False, null=False)
    defaultsearchstr = models.TextField(null=True, blank=True)
    imdb_id = models.TextField(null=True, blank=True)
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

    @property
    def remotePath(self):
        return self.remotepathstr

    @property
    def displayName(self):
        return self.shortName.replace('.',' ').title()

    def __unicode__(self):
        return 'id: %s r: %s l: %s' % (self.id, self.remotePath, self.localPath)

    def lastCreatedFileDateForSpan(self):
        last_date = self.lastCreatedFileDate
        return last_date and last_date.isoformat()

    @classmethod
    def distinctShowFolders(cls):
        moviePath = Path.objects.get(pk=MOVIE_PATH_ID)
        refFiles = File.objects.exclude(path=moviePath).order_by('path').distinct('path').select_related('path')
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
        return self.localpathstr == MOVIE and self.remotepathstr == MOVIE

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
            if 'Response' in data and data['Response'] == 'False':
                imdbFailure = True

            if not imdbFailure:
                log.info('Using IMDB data')
                imgName = data['Poster'].rpartition('/')[-1]
                saveImageToDisk(data['Poster'], imgName)
                poster.image = imgName

                assignDataToPoster(data, poster)

                data = getDataFromIMDBByPath(self, useExtendedPlot=True)
                assignDataToPoster(data, poster, onlyExtendedPlot=True)
            else:
                log.info('IMDB failed. Attempting to use TVDB.')
                tvinfo = searchTVDBByName(self.defaultsearchstr)
                if tvinfo:
                    self.tvdb_id = tvinfo['results'][0]['id']
                    result = tvinfo['results'][0]
                    poster_path = result.get('poster_path', None)
                    if poster_path:
                        imgName = poster_path.rpartition('/')[-1]
                        posterURL = '%s/%s/%s' % (tvdbConfig.url, tvdbConfig.still_size, imgName)
                        saveImageToDisk(posterURL, imgName)
                        poster.image = imgName
                assignDataToPoster({}, poster, foundNone=True)
        except Exception, e:
            log.error(str(e), exc_info=True)
            assignDataToPoster({}, poster, foundNone=True)
        poster.save()
        return poster

    def _posterfileget(self):
        try:
            posterfile = PosterFile.objects.get(path=self)
        except:
            posterfile = None
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

    # TODO: Finish this method after converting datestrs to actual datetimes
    #def unwatched_tv_shows_since_date(self, user):
        #if self.isMovie():
            #raise Exception('This function does not apply to movies')
#
        #files = (File.objects.filter(path=self)
