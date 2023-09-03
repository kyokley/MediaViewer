"""
Re-implementation of PosterFile
"""
from django.db import models
from mediaviewer.core import TimeStampModel
from mediaviewer.log import log
# from mediaviewer.models.genre import Genre
# from mediaviewer.models.actor import Actor
# from mediaviewer.models.writer import Writer
# from mediaviewer.models.director import Director
from mediaviewer.models.tvdbconfiguration import (
    getDataFromIMDB,
    getDataFromIMDBByPath,
    saveImageToDisk,
    searchTVDBByName,
    tvdbConfig,
    getTVDBEpisodeInfo,
    getCastData,
    getExtendedInfo,
    getJSONData,
)
from django.conf import settings


def _getDataFromIMDBByID(imdb_id, is_movie=True):
    log.debug(f"Getting data from IMDB using {imdb_id}")

    url = f"https://api.themoviedb.org/3/find/{imdb_id}?api_key={settings.API_KEY}&external_source=imdb_id"
    resp = getJSONData(url)

    if resp:
        if not is_movie:
            if resp.get("tv_results"):
                tmdb_id = resp.get("tv_results")[0]["id"]
            elif resp.get("tv_episode_results"):
                tmdb_id = resp.get("tv_episode_results")[0]["id"]

            url = f"https://api.themoviedb.org/3/tv/{tmdb_id}?api_key={settings.API_KEY}"
        else:
            tmdb_id = resp.get("movie_results")[0]["id"]
            url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={settings.API_KEY}"

        data = getJSONData(url)

        if data:
            data["url"] = url
        else:
            return None
        return data


class Poster(TimeStampModel):
    plot = models.TextField(blank=True, null=False, default='')
    extendedplot = models.TextField(blank=True, null=False, default='')
    genres = models.ManyToManyField("mediaviewer.Genre", blank=True)
    actors = models.ManyToManyField("mediaviewer.Actor", blank=True)
    writers = models.ManyToManyField("mediaviewer.Writer", blank=True)
    directors = models.ManyToManyField("mediaviewer.Director", blank=True)
    episodename = models.CharField(blank=True, null=False, default='', max_length=100)
    rated = models.CharField(blank=True, null=False, default='', max_length=100)
    rating = models.CharField(blank=True, null=False, default='', max_length=32)
    tmdb = models.CharField(blank=True, null=False, default='', max_length=32)
    image = models.ImageField(upload_to='uploads/%Y/%m/%d/')
    tagline = models.CharField(blank=True, null=False, default='', max_length=100)

    @property
    def media(self):
        if not getattr(self, '_media', None):
            self._media = self.tv_set.first() or self.movie_set.first()
        return self._media

    @property
    def name(self):
        return self.media.name

    def display_genres(self):
        return ", ".join([x.genre for x in self.genres.all()])

    def display_actors(self):
        return ", ".join([x.name for x in self.actors.order_by("order").all()])

    def display_writers(self):
        return ", ".join([x.name for x in self.writers.all()])

    def display_directors(self):
        return ", ".join([x.name for x in self.directors.all()])

    def _getIMDBData(self):
        log.debug("Attempt to get data from IMDB")

        if self.media.is_movie():
            data = getDataFromIMDB(self.media)
        elif self.path:
            data = getDataFromIMDBByPath(self.media)
        else:
            data = getDataFromIMDB(self.media)

        if data:
            self.tmdb_id = data["id"]

            self.poster_url = data.get("Poster") or data.get("poster_path")
            self._cast_and_crew()
            self._store_extended_info()
            self._store_plot(data)
            self._store_genres(data)
            self._store_rated(data)
        self._assign_tvdb_info()

        return data
