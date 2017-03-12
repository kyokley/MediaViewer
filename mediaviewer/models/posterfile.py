from django.db import models
from mediaviewer.log import log

from mediaviewer.models.tvdbconfiguration import (getDataFromIMDB,
                                                  getDataFromIMDBByPath,
                                                  saveImageToDisk,
                                                  searchTVDBByName,
                                                  tvdbConfig,
                                                  getTVDBEpisodeInfo,
                                                  getCastData,
                                                  getRating,
                                                  )
from mediaviewer.models.genre import Genre
from mediaviewer.models.actor import Actor
from mediaviewer.models.writer import Writer
from mediaviewer.models.director import Director

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
    tmdb_id = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'posterfile'

    def __unicode__(self):
        return 'id: %s f: %s i: %s' % (self.id, self.file and self.file.filename or self.path and self.path.localpathstr, self.image)

    def display_genres(self):
        return ', '.join([x.genre for x in self.genres.all()])

    def display_actors(self):
        return ', '.join([x.name for x in self.actors.order_by('order').all()])

    def display_writers(self):
        return ', '.join([x.name for x in self.writers.all()])

    def display_directors(self):
        return ', '.join([x.name for x in self.directors.all()])

    @classmethod
    def new(cls,
            file=None,
            path=None):
        if not file and not path or (file and path):
            raise ValueError('Either file or path must be defined')

        if path and path.isMovie():
            raise ValueError('Movie paths are not allowed to have poster data')

        if file:
            existing = cls.objects.filter(file=file).first()
            if existing:
                return existing

        if path:
            existing = cls.objects.filter(path=path).first()
            if existing:
                return existing

        log.info('PosterFile not found. Creating a new one')
        obj = cls()
        obj.file = file
        obj.path = path
        obj.save()

        obj._downloadPosterData()
        return obj

    def _downloadPosterData(self):
        if self.path and self.path.isMovie():
            raise ValueError('Movie paths are not allowed to have poster data')

        ref_obj = self.file or self.path

        log.debug('Downloading poster data')
        log.info('Getting poster data for %s' % (self,))

        imgName = ''
        if ref_obj.isMovie():
            log.debug('This is a movie file. '
                      'Set season and episode to None')
            season = None
            episode = None

            log.debug('Attempt to get data from IMDB')
            data = getDataFromIMDB(ref_obj)
        elif self.path:
            log.debug('This is a path for a tv show'
                      'Set season and episode to None')
            season = None
            episode = None

            log.debug('Attempt to get data from IMDB')
            data = getDataFromIMDBByPath(ref_obj)
        else:
            log.debug('Getting season and episode')
            season = ref_obj.getScrapedSeason()
            season = season and int(season)
            episode = ref_obj.getScrapedEpisode()
            episode = episode and int(episode)

            log.debug('Attempt to get data from IMDB')
            data = getDataFromIMDB(ref_obj)

        if data:
            log.debug('Received data from IMDB')
            self.tmdb_id = data['id']

            cast_and_crew = getCastData(self.tmdb_id,
                                        season=season,
                                        episode=episode,
                                        isMovie=ref_obj.isMovie())
            try:
                posterURL = data.get('Poster') or data.get('poster_path')
            except Exception as e:
                log.error(e)
                posterURL = None
        else:
            log.debug('Failed to receive data from IMDB')
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

                try:
                    tvdb_id = tvinfo['results'][0]['id'] if tvinfo else None
                except Exception as e:
                    log.error('Got bad response during searchTVDBByName: {}'.format(ref_obj.searchString()))
                    log.error(e)
                    tvdb_id = None

                if tvdb_id:
                    log.debug('Set tvdb id for this path to {}'.format(tvdb_id))
                    ref_obj.path.tvdb_id = tvdb_id
                    ref_obj.path.save()
            else:
                tvdb_id = ref_obj.path.tvdb_id

            if tvdb_id:
                tvinfo = getTVDBEpisodeInfo(tvdb_id,
                                            season,
                                            episode)
            else:
                tvinfo = None

            if tvinfo:
                posterURL = tvinfo.get('still_path')
                imgName = posterURL.rpartition('/')[-1]
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
            self._assignDataToPoster(data, cast_and_crew, ref_obj)

        self.save()
        log.debug('Done getting poster data')
        return self

    def _assignDataToPoster(self, data, cast_and_crew, ref_obj):
        plot = (data.get('Plot') or
                    data.get('overview') or
                    'results' in data and data['results'] and data['results'][0].get('overview'))
        self.plot = plot if plot and plot != 'undefined' else None

        if data.get('results') or data.get('genre_ids'):
            genre_ids = data.get('genre_ids') or data['results'][0]['genre_ids']
            for genre_id in genre_ids:
                g = tvdbConfig.genres.get(genre_id)
                if g:
                    genre_obj = Genre.new(g)
                    self.genres.add(genre_obj)
                else:
                    log.warn('Genre for ID = {} not found'.format(genre_id))
        elif data.get('genres'):
            for genre in data.get('genres'):
                genre_obj = Genre.new(genre['name'])
                self.genres.add(genre_obj)

        for actor in cast_and_crew['cast']:
            actor_obj = Actor.new(actor['name'], order=actor.get('order'))
            self.actors.add(actor_obj)

        for job in cast_and_crew['crew']:
            if job['job'] == 'Writer':
                writer_obj = Writer.new(job['name'])
                self.writers.add(writer_obj)
            elif job['job'] == 'Director':
                director_obj = Director.new(job['name'])
                self.directors.add(director_obj)

        rating = getRating(self.tmdb_id, isMovie=ref_obj.isMovie())
        self.rating = rating if rating and rating != 'undefined' else None
        rated = data.get('Rated')
        self.rated = rated if rated and rated != 'undefined' else None
