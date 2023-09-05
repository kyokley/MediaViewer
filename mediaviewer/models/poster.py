"""
Re-implementation of PosterFile
"""
from django.db import models
from mediaviewer.core import TimeStampModel
from mediaviewer.log import log
from mediaviewer.models.genre import Genre
from mediaviewer.models.actor import Actor
from mediaviewer.models.writer import Writer
from mediaviewer.models.director import Director
from mediaviewer.models.tvdbconfiguration import (
    getDataFromIMDB,
    getDataFromIMDBByPath,
    saveImageToDisk,
    searchTVDBByName,
    tvdbConfig,
    getTVDBEpisodeInfo,
    getJSONData,
)
from django.conf import settings


def _get_data_from_imdb(media):
    log.debug(f"Getting data from IMDB using {media.imdb}")

    url = f"https://api.themoviedb.org/3/find/{media.imdb}?api_key={settings.API_KEY}&external_source=media.imdb"
    resp = getJSONData(url)

    if resp:
        if not media.is_movie():
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


def _getDataFromIMDBBySearchString(searchString, is_movie=True):
    log.debug(f"Getting data from IMDB using {searchString}")

    if not is_movie:
        url = f"https://api.themoviedb.org/3/search/tv?query={searchString}&api_key={settings.API_KEY}"  # noqa
    else:
        url = f"https://api.themoviedb.org/3/search/movie?query={searchString}&api_key={settings.API_KEY}"  # noqa

    data = getJSONData(url)
    data = (
        data["results"][0]
        if data and data.get("results") and data.get("results")[0]
        else None
    )
    if data:
        data["url"] = url
    else:
        return None
    return data


def _get_cast_data(tmdb_id, season=None, episode=None, is_movie=True):
    log.debug("Getting data from TVDb using %s" % (tmdb_id,))

    if not is_movie:
        if episode and season:
            url = "https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season}/episode/{episode}/credits?api_key={api_key}".format(  # noqa
                season=season,
                episode=episode,
                tmdb_id=tmdb_id,
                api_key=settings.API_KEY,
            )
        else:
            url = "https://api.themoviedb.org/3/tv/{tmdb_id}/credits?api_key={api_key}".format(  # noqa
                tmdb_id=tmdb_id, api_key=settings.API_KEY
            )
    else:
        url = "https://api.themoviedb.org/3/movie/{tmdb_id}/credits?api_key={api_key}".format(  # noqa
            tmdb_id=tmdb_id, api_key=settings.API_KEY
        )

    return getJSONData(url)


def _get_extended_info(tmdb_id, is_movie=True):
    log.debug("Getting IMDB rating for tmdb_id = %s" % tmdb_id)

    if not is_movie:
        url = "https://api.themoviedb.org/3/tv/{tmdb_id}/external_ids?api_key={api_key}".format(  # noqa
            tmdb_id=tmdb_id, api_key=settings.API_KEY
        )
    else:
        url = "https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={api_key}".format(  # noqa
            tmdb_id=tmdb_id, api_key=settings.API_KEY
        )

    data = getJSONData(url)
    return data


class PosterManager(models.Manager):
    def create_from_media(self, media):
        poster = self.__model__()

        data = _get_data_from_imdb(media)

        poster.save()
        return poster


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

    objects = PosterManager()

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

    def _get_imdb_data(self):
        log.debug("Attempt to get data from IMDB")

        data = _get_data_from_imdb(self.media)

        if data:
            self.tmdb = data["id"]

            self.poster_url = data.get("Poster") or data.get("poster_path")
            self._cast_and_crew()
            self._store_extended_info()
            self._store_plot(data)
            self._store_genres(data)
            self._store_rated(data)
        self._assign_tvdb_info()

        return data

    def _assign_tvdb_info(self):
        if self.media.is_movie() or not self.media.season or not self.media.episode:
            return

        # Having season and episode implies that we must be a tv file
        if self.ref_obj.path and not self.ref_obj.path.tvdb_id:
            log.debug("No tvdb id for this path. " "Continue search by tv show name")
            tvinfo = searchTVDBByName(self.ref_obj.searchString())

            try:
                tvdb_id = tvinfo["results"][0]["id"] if tvinfo else None
            except Exception as e:
                log.error(
                    "Got bad response during searchTVDBByName: {}".format(
                        self.ref_obj.searchString()
                    )
                )
                log.error(e)
                tvdb_id = None

            if tvdb_id:
                log.debug("Set tvdb id for this path to {}".format(tvdb_id))
                self.ref_obj.path.tvdb_id = tvdb_id
                self.ref_obj.path.save()
        elif self.ref_obj.path:
            tvdb_id = self.ref_obj.path.tvdb_id
        else:
            tvdb_id = None

        if tvdb_id:
            self._tvdb_episode_info(tvdb_id)

    def _store_plot(self, imdb_data):
        plot = (
            imdb_data.get("Plot")
            or imdb_data.get("overview")
            or "results" in imdb_data
            and imdb_data["results"]
            and imdb_data["results"][0].get("overview")
        )
        self.plot = plot if plot and plot != "undefined" else None

    def _store_extended_info(self):
        extended_info = _get_extended_info(self.tmdb, is_movie=self.media.is_movie())

        self._store_rating(extended_info)
        self._store_tagline(extended_info)

    def _store_tagline(self, extended_info):
        tagline = extended_info.get("tagline")
        self.tagline = tagline if tagline and tagline != "undefined" else None

    def _store_rating(self, extended_info):
        rating = extended_info.get("imdbRating") or extended_info.get("vote_average")
        self.rating = rating if rating and rating != "undefined" else None

    def _store_rated(self, imdb_data):
        rated = imdb_data.get("Rated")
        self.rated = rated if rated and rated != "undefined" else None

    def _store_genres(self, imdb_data):
        if imdb_data.get("results") or imdb_data.get("genre_ids"):
            genre_ids = (
                imdb_data.get("genre_ids") or imdb_data["results"][0]["genre_ids"]
            )
            for genre_id in genre_ids:
                g = tvdbConfig.genres.get(genre_id)
                if g:
                    genre_obj = Genre.new(g)
                    self.genres.add(genre_obj)
                else:
                    log.warn("Genre for ID = {} not found".format(genre_id))
        elif imdb_data.get("genres"):
            for genre in imdb_data.get("genres"):
                genre_obj = Genre.new(genre["name"])
                self.genres.add(genre_obj)

    def _cast_and_crew(self):
        """Populate cast and crew info for this posterfile."""
        cast_and_crew = _get_cast_data(
            self.tmdb,
            season=self.season,
            episode=self.episode,
            is_movie=self.media.is_movie(),
        )

        if cast_and_crew:
            for actor in cast_and_crew["cast"]:
                actor_obj = Actor.objects.create(
                    name=actor["name"], order=actor.get("order")
                )
                self.actors.add(actor_obj)

            for job in cast_and_crew["crew"]:
                if job["job"] == "Writer":
                    writer_obj = Writer.objects.create(name=job["name"])
                    self.writers.add(writer_obj)
                elif job["job"] == "Director":
                    director_obj = Director.objects.create(name=job["name"])
                    self.directors.add(director_obj)
