from django.db import models
from mediaviewer.log import log

from mediaviewer.models.tvdbconfiguration import (getDataFromIMDB,
                                                  getDataFromIMDBByPath,
                                                  saveImageToDisk,
                                                  searchTVDBByName,
                                                  tvdbConfig,
                                                  getTVDBEpisodeInfo,
                                                  getCastData,
                                                  getExtendedInfo,
                                                  )
from mediaviewer.models.genre import Genre
from mediaviewer.models.actor import Actor
from mediaviewer.models.writer import Writer
from mediaviewer.models.director import Director


# Destroy failed posterfiles weekly to allow new attempts
class PosterFile(models.Model):
    file = models.ForeignKey('mediaviewer.File',
                             on_delete=models.CASCADE,
                             null=True,
                             db_column='fileid',
                             blank=True,
                             related_name='_posterfile')
    path = models.ForeignKey('mediaviewer.Path',
                             on_delete=models.CASCADE,
                             null=True,
                             db_column='pathid',
                             blank=True,
                             related_name='_posterfile')
    datecreated = models.DateTimeField(db_column='datecreated',
                                       blank=True,
                                       auto_now_add=True)
    dateedited = models.DateTimeField(db_column='dateedited',
                                      blank=True,
                                      auto_now=True)
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
    poster_url = models.URLField(blank=True, null=True)
    tagline = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'posterfile'

    def __str__(self):
        return 'id: %s f: %s i: %s' % (
                self.id,
                self.filename or self.pathname,
                self.image)

    @property
    def filename(self):
        return self.file and self.file.displayName()

    @property
    def pathname(self):
        return self.path and self.path.remotepathstr

    def display_genres(self):
        return ', '.join([x.genre for x in self.genres.all()])

    def display_actors(self):
        return ', '.join([x.name for x in self.actors.order_by('order').all()])

    def display_writers(self):
        return ', '.join([x.name for x in self.writers.all()])

    def display_directors(self):
        return ', '.join([x.name for x in self.directors.all()])

    @property
    def image(self):
        return self.poster_url.rpartition('/')[-1] if self.poster_url else None

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

        obj._populate_poster_data()
        obj.save()
        return obj

    @property
    def ref_obj(self):
        return self.file or self.path

    @property
    def season(self):
        if self.file and self.file.isTVShow():
            scraped_season = self.ref_obj.getScrapedSeason()
            return int(scraped_season) if scraped_season else None
        else:
            return None

    @property
    def episode(self):
        if self.file and self.file.isTVShow():
            scraped_episode = self.ref_obj.getScrapedEpisode()
            return int(scraped_episode) if scraped_episode else None
        else:
            return None

    def _populate_poster_data(self):
        self._getIMDBData()
        self._download_poster()

    def _download_poster(self):
        try:
            if self.poster_url:
                saveImageToDisk(self.poster_url, self.image)
        except Exception as e:
            log.error(str(e), exc_info=True)
            log.error('Failed to download image')

    def _getIMDBData(self):
        log.debug('Attempt to get data from IMDB')

        if self.ref_obj.isMovie():
            data = getDataFromIMDB(self.ref_obj)
        elif self.path:
            data = getDataFromIMDBByPath(self.ref_obj)
        else:
            data = getDataFromIMDB(self.ref_obj)

        if data:
            self.tmdb_id = data['id']

            self.poster_url = data.get('Poster') or data.get('poster_path')
            self._cast_and_crew()
            self._store_extended_info()
            self._store_plot(data)
            self._store_genres(data)
            self._store_rated(data)
        self._assign_tvdb_info()

        return data

    def _store_plot(self, imdb_data):
        plot = (
            imdb_data.get('Plot') or
            imdb_data.get('overview') or
            'results' in imdb_data and
            imdb_data['results'] and imdb_data['results'][0].get('overview'))
        self.plot = plot if plot and plot != 'undefined' else None

    def _store_genres(self, imdb_data):
        if imdb_data.get('results') or imdb_data.get('genre_ids'):
            genre_ids = (imdb_data.get('genre_ids') or
                         imdb_data['results'][0]['genre_ids'])
            for genre_id in genre_ids:
                g = tvdbConfig.genres.get(genre_id)
                if g:
                    genre_obj = Genre.new(g)
                    self.genres.add(genre_obj)
                else:
                    log.warn('Genre for ID = {} not found'.format(genre_id))
        elif imdb_data.get('genres'):
            for genre in imdb_data.get('genres'):
                genre_obj = Genre.new(genre['name'])
                self.genres.add(genre_obj)

    def _store_extended_info(self):
        extended_info = getExtendedInfo(
                self.tmdb_id,
                isMovie=self.ref_obj.isMovie())

        self._store_rating(extended_info)
        self._store_tagline(extended_info)

    def _store_tagline(self, extended_info):
        tagline = extended_info.get('tagline')
        self.tagline = tagline if tagline and tagline != 'undefined' else None

    def _store_rating(self, extended_info):
        rating = (extended_info.get('imdbRating') or
                  extended_info.get('vote_average'))
        self.rating = rating if rating and rating != 'undefined' else None

    def _store_rated(self, imdb_data):
        rated = imdb_data.get('Rated')
        self.rated = rated if rated and rated != 'undefined' else None

    def _cast_and_crew(self):
        """Populate cast and crew info for this posterfile. """
        cast_and_crew = getCastData(self.tmdb_id,
                                    season=self.season,
                                    episode=self.episode,
                                    isMovie=self.ref_obj.isMovie())

        if cast_and_crew:
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

    def _tvdb_episode_info(self, tvdb_id):
        tvinfo = getTVDBEpisodeInfo(tvdb_id,
                                    self.season,
                                    self.episode)

        if tvinfo:
            self.poster_url = tvinfo.get('still_path') or self.poster_url
            self.extendedplot = tvinfo.get('overview', '')
            self.episodename = tvinfo.get('name')

    def _assign_tvdb_info(self):
        if not self.season or not self.episode:
            return

        # Having season and episode implies that we must be a tv file
        if self.ref_obj.path and not self.ref_obj.path.tvdb_id:
            log.debug('No tvdb id for this path. '
                      'Continue search by tv show name')
            tvinfo = searchTVDBByName(self.ref_obj.searchString())

            try:
                tvdb_id = tvinfo['results'][0]['id'] if tvinfo else None
            except Exception as e:
                log.error(
                    'Got bad response during searchTVDBByName: {}'.format(
                        self.ref_obj.searchString()))
                log.error(e)
                tvdb_id = None

            if tvdb_id:
                log.debug(
                        'Set tvdb id for this path to {}'.format(tvdb_id))
                self.ref_obj.path.tvdb_id = tvdb_id
                self.ref_obj.path.save()
        elif self.ref_obj.path:
            tvdb_id = self.ref_obj.path.tvdb_id
        else:
            tvdb_id = None

        if tvdb_id:
            self._tvdb_episode_info(tvdb_id)
