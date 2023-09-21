"""
Re-implementation of PosterFile
"""
from io import BytesIO
import requests
from django.db import models
from .core import TimeStampModel
from mediaviewer.log import log
from .genre import Genre
from .actor import Actor
from .writer import Writer
from .director import Director
from .tvdbconfiguration import (
    tvdbConfig,
    getTVDBEpisodeInfo,
    getJSONData,
)
from django.core.files.images import ImageFile
from django.conf import settings


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


def _search_TVDB_by_name(name):
    if not tvdbConfig.connected:
        return {}

    name = name.replace("&", "%26")
    name = name.replace(",", "%2C")
    name = name.replace("+", "%2B")

    url = (
        f"https://api.themoviedb.org/3/search/tv?query={name}&api_key={settings.API_KEY}")
    return getJSONData(url)


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
    def create_from_ref_obj(self, ref_obj, imdb='', tmdb=''):
        new_poster = self.model()
        new_poster.imdb = imdb
        new_poster.tmdb = tmdb
        new_poster.save()

        ref_obj.poster = new_poster
        ref_obj.save()
        return new_poster


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
    tmdb = models.CharField(null=False,
                            default='',
                            blank=True,
                            max_length=32)
    imdb = models.CharField(null=False,
                            default='',
                            blank=True,
                            max_length=32)
    image = models.ImageField(upload_to='uploads/%Y/%m/%d/')
    tagline = models.CharField(blank=True, null=False, default='', max_length=100)

    objects = PosterManager()

    @property
    def season(self):
        return getattr(self.ref_obj, 'season', None)

    @property
    def episode(self):
        return getattr(self.ref_obj, 'episode', None)

    @property
    def ref_obj(self):
        """
        Reference object for this Poster.

        This object will be one of a MediaFile, TV, or Movie.
        """
        if not getattr(self, '_ref_obj', None):
            self._ref_obj = getattr(self, 'media_file', None) or getattr(self, 'tv', None) or getattr(self, 'movie', None)
            if self._ref_obj is None:
                raise Exception(f'{self} has no media_file, tv, or movie')
        return self._ref_obj

    @property
    def name(self):
        return self.ref_obj.full_name

    def display_genres(self):
        return ", ".join([x.genre for x in self.genres.all()])

    def display_actors(self):
        return ", ".join([x.name for x in self.actors.order_by("order").all()])

    def display_writers(self):
        return ", ".join([x.name for x in self.writers.all()])

    def display_directors(self):
        return ", ".join([x.name for x in self.directors.all()])

    def _get_data_from_imdb(self):
        if self.tmdb:
            log.debug(f"Getting data from TVDB using {self.tmdb}")

            if self.ref_obj.is_movie():
                url = f"https://api.themoviedb.org/3/movie/{self.tmdb}?language=en-US&api_key={settings.API_KEY}"
            else:
                url = f"https://api.themoviedb.org/3/tv/{self.tmdb}?language=en-US&api_key={settings.API_KEY}"
        elif self.imdb:
            log.debug(f"Getting data from IMDB using {self.imdb}")

            url = f"https://api.themoviedb.org/3/find/{self.imdb}?api_key={settings.API_KEY}&external_source=imdb_id"
        else:
            if self.ref_obj.is_movie():
                url = f"https://api.themoviedb.org/3/search/movie?query={self.name}&api_key={settings.API_KEY}"
            else:
                url = f"https://api.themoviedb.org/3/search/tv?query={self.name}&api_key={settings.API_KEY}"
        resp = getJSONData(url)

        if self.tmdb:
            resp['url'] = url
            return resp
        if resp:
            tmdb_id = None
            if not self.ref_obj.is_movie():
                if resp.get("tv_results"):
                    tmdb_id = resp.get("tv_results")[0]["id"]
                elif resp.get("tv_episode_results"):
                    tmdb_id = resp.get("tv_episode_results")[0]["id"]

                url = f"https://api.themoviedb.org/3/tv/{tmdb_id}?api_key={settings.API_KEY}"
            else:
                tmdb_id = resp.get("movie_results")[0]["id"]
                url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={settings.API_KEY}"

            if tmdb_id:
                data = getJSONData(url)
                self.tmdb = tmdb_id

            if data:
                data["url"] = url
            else:
                return None
            return data

    def _populate_data(self):
        log.debug("Attempt to get data from IMDB")

        data = self._get_data_from_imdb()

        if not data:
            return None

        self.tmdb = data["id"]

        self._cast_and_crew()
        self._store_extended_info()
        self._store_plot(data)
        self._store_genres(data)
        self._store_rated(data)
        self._assign_tmdb_info()

        poster_url = data.get("Poster") or data.get("poster_path")
        poster_name = poster_url.rpartition("/")[-1] if poster_url else None

        if poster_name:
            r = requests.get(
                "{url}{poster_size}{path}".format(
                    url=tvdbConfig.url, poster_size=tvdbConfig.poster_size, path=poster_url
                ),
                stream=True,
                timeout=settings.REQUEST_TIMEOUT,
            )
            r.raise_for_status()

            io = BytesIO()

            if r.status_code == 200:
                for chunk in r.iter_content(1024):
                    io.write(chunk)

                io.seek(0)

                image = ImageFile(io, name=poster_name)
                self.image = image

        return data

    def _assign_tmdb_info(self):
        if self.ref_obj.is_movie() or self.season is None or self.episode is None:
            return

        # Having season and episode implies that we must be a tv file
        if not self.tmdb:
            log.debug("No tmdb id for this path. " "Continue search by tv show name")
            tvinfo = _search_TVDB_by_name(self.ref_obj.display_name)

            try:
                tmdb_id = tvinfo["results"][0]["id"] if tvinfo else None
            except Exception as e:
                log.error(
                    f"Got bad response during _search_TVDB_by_name: {self.ref_obj.display_name}")
                log.error(e)
                tmdb_id = None

            if tmdb_id:
                log.debug("Set tmdb id for this path to {}".format(tmdb_id))
                self.tmdb = tmdb_id

        self._tmdb_episode_info(self.tmdb)

    def _tmdb_episode_info(self, tmdb_id):
        if not tmdb_id:
            return None

        tvinfo = getTVDBEpisodeInfo(tmdb_id, self.season, self.episode)

        if tvinfo:
            self.poster_url = tvinfo.get("still_path") or self.poster_url
            self.extendedplot = tvinfo.get("overview", "")
            self.episodename = tvinfo.get("name")
            self.tmdb = tvinfo.get('id', self.tmdb)

    def _store_plot(self, imdb_data):
        plot = (
            imdb_data.get("Plot")
            or imdb_data.get("overview")
            or "results" in imdb_data
            and imdb_data["results"]
            and imdb_data["results"][0].get("overview")
        )
        self.plot = plot if plot and plot != "undefined" else ''

    def _store_extended_info(self):
        extended_info = _get_extended_info(self.tmdb, is_movie=self.ref_obj.is_movie())

        self._store_rating(extended_info)
        self._store_tagline(extended_info)

    def _store_tagline(self, extended_info):
        tagline = extended_info.get("tagline")
        self.tagline = tagline if tagline and tagline != "undefined" else ''

    def _store_rating(self, extended_info):
        rating = extended_info.get("imdbRating") or extended_info.get("vote_average")
        self.rating = rating if rating and rating != "undefined" else ''

    def _store_rated(self, imdb_data):
        rated = imdb_data.get("Rated")
        self.rated = rated if rated and rated != "undefined" else ''

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
            is_movie=self.ref_obj.is_movie(),
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
