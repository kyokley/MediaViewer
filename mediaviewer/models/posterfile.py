from django.db import models
from mediaviewer.log import log

from mediaviewer.models.tvdbconfiguration import (getDataFromIMDB,
                                                  saveImageToDisk,
                                                  assignDataToPoster,
                                                  searchTVDBByName,
                                                  tvdbConfig,
                                                  getTVDBEpisodeInfo,
                                                  )
from mediaviewer.models.genre import Genre

#TODO: Add column to track tvdb and omdb success
# Destroy failed posterfiles weekly to allow new attempts
class PosterFile(models.Model):
    file = models.ForeignKey('mediaviewer.File', null=True, db_column='fileid', blank=True, related_name='_posterfile')
    path = models.ForeignKey('mediaviewer.Path', null=True, db_column='pathid', blank=True, related_name='_posterfile')
    datecreated = models.DateTimeField(db_column='datecreated', blank=True, auto_now_add=True)
    dateedited = models.DateTimeField(db_column='dateedited', blank=True, auto_now=True)
    image = models.TextField(blank=True)
    plot = models.TextField(blank=True)
    extendedplot = models.TextField(blank=True)
    genres = models.ManyToManyField('mediaviewer.Genre')
    actors = models.ManyToManyField('mediaviewer.Actor')
    writers = models.ManyToManyField('mediaviewer.Writer')
    directors = models.ManyToManyField('mediaviewer.Director')
    episodename = models.TextField(blank=True, null=True)
    rated = models.TextField(blank=True, null=True)
    rating = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'posterfile'

    def __unicode__(self):
        return 'id: %s f: %s i: %s' % (self.id, self.file and self.file.filename or self.path and self.path.localpathstr, self.image)

    @classmethod
    def new(cls,
            file=None,
            path=None):
        if not file and not path or (file and path):
            raise ValueError('Either file or path must be defined')

        obj = cls()
        obj.file = file
        obj.path = path
        obj.save()

        obj._downloadPosterData()
        return obj

    def _downloadPosterData(self):
        log.debug('Downloading poster data')
        log.info('Getting poster data for %s' % (self,))

        ref_obj = self.file or self.path
        try:
            imgName = ''
            if ref_obj.isMovie():
                log.debug('This is a movie file. '
                          'Set season and episode to None')
                season = None
                episode = None
            else:
                log.debug('Getting season and episode')
                season = ref_obj.getScrapedSeason()
                season = season and int(season)
                episode = ref_obj.getScrapedEpisode()
                episode = episode and int(episode)

            log.debug('Attempt to get data from IMDB')
            data = getDataFromIMDB(ref_obj, useExtendedPlot=True)

            if data:
                log.debug('Received data from IMDB')
                posterURL = data.get('Poster')
            else:
                posterURL = None

            if posterURL:
                imgName = posterURL.rpartition('/')[-1]
            else:
                log.info('Failed to get poster url from IMDB for %s' % (ref_obj,))

            if not season or not episode:
                log.debug('Skipping tvdb search')
            else:
                if ref_obj.path and not ref_obj.path.tvdb_id:
                    log.debug('No tvdb id for this path.'
                              'Continue search by tv show name')
                    tvinfo = searchTVDBByName(ref_obj.searchString())
                    tvdb_id = tvinfo['results'][0]['id']
                    log.debug('Set tvdb id for this path')
                    ref_obj.path.tvdb_id = tvdb_id
                    ref_obj.path.save()
                else:
                    tvdb_id = ref_obj.path.tvdb_id
                tvinfo = getTVDBEpisodeInfo(tvdb_id,
                                            season,
                                            episode)

                if tvinfo:
                    still_path = tvinfo.get('still_path')
                    if still_path:
                        imgName = still_path.rpartition('/')[-1]
                        posterURL = '%s/%s/%s' % (tvdbConfig.url,
                                                  tvdbConfig.still_size,
                                                  imgName)
                    self.extendedplot = tvinfo.get('overview', '')
                    self.episodename = tvinfo.get('name')

            if posterURL:
                if data:
                    data['Poster'] = posterURL
                try:
                    saveImageToDisk(posterURL, imgName)
                    self.image = imgName
                except Exception, e:
                    log.error(str(e), exc_info=True)
                    log.error('Failed to download image')

            if data:
                assignDataToPoster(data, self)

            if not self.extendedplot:
                log.debug('No extended plot from TVDB. Getting info from IMDB')
                data = getDataFromIMDB(ref_obj, useExtendedPlot=True)
                assignDataToPoster(data, self, onlyExtendedPlot=True)
        except Exception, e:
            log.error(str(e), exc_info=True)
            assignDataToPoster({}, self, foundNone=True)
        self.save()
        log.debug('Done getting poster data')

        if ref_obj.isMovie():
            ref_obj.populate_genres(clearExisting=True)
        return self

    def _assignDataToPoster(self, data, onlyExtendedPlot=False):
        if not onlyExtendedPlot:
            plot = data.get('Plot') or data.get('overview')
            self.plot = (not plot or plot == 'undefined') and 'Plot not found' or plot
            genre = data.get('Genre')
            genre = (not genre or genre == 'undefined') and None or genre
            if genre:
                genres = genre.split(', ')
                for g in genres:
                    genre_obj = Genre.new(g)
                    self.genres.add(genre_obj)

            actors = data.get('Actors')
            self.actors = (not actors or actors == 'undefined') and 'Actors not found' or actors
            writer = data.get('Writer')
            self.writer = (not writer or writer == 'undefined') and 'Writer not found' or writer
            director = data.get('Director')
            self.director = (not director or director == 'undefined') and 'Director not found' or director
            rating = data.get('imdbRating')
            self.rating = rating != 'undefined' and rating or None
            rated = data.get('Rated')
            self.rated = rated != 'undefined' and rated or None
        else:
            self.extendedplot = (not data.get('Plot', None) or data.get('Plot', None) == 'undefined') and 'Plot not found' or data.get('Plot', None)
