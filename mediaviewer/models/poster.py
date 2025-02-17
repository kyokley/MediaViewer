"""
Re-implementation of PosterFile
"""

from datetime import date
from io import BytesIO

import requests
from django.conf import settings
from django.contrib import admin
from django.core.files.images import ImageFile
from django.db import models

from mediaviewer.log import log

from .actor import Actor
from .core import TimeStampModel
from .director import Director
from .genre import Genre
from .tvdbconfiguration import getJSONData, getTVDBEpisodeInfo, tvdbConfig
from .writer import Writer

SENTINEL = object()


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

    url = f"https://api.themoviedb.org/3/search/tv?query={name}&api_key={settings.API_KEY}"
    return getJSONData(url)


def _get_cast_data(tmdb_id, season=None, episode=None, is_movie=True):
    log.info("Getting data from TVDb using %s" % (tmdb_id,))
    if not tmdb_id:
        log.warn("Skipping getting data: tmdb_id is null.")
        return {}

    urls = []

    if not is_movie:
        if episode and season:
            urls.append(
                f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season}/episode/{episode}/credits?api_key={settings.API_KEY}"
            )

        if season:
            urls.append(
                f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season}/credits?api_key={settings.API_KEY}"
            )

        urls.append(
            f"https://api.themoviedb.org/3/tv/{tmdb_id}/credits?api_key={settings.API_KEY}"
        )
    else:
        urls.append(
            f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits?api_key={settings.API_KEY}"
        )

    resp = None
    for url in urls:
        try:
            resp = getJSONData(url)
        except Exception as e:
            log.debug(e)
            continue

        if resp:
            break
    return resp


def _get_extended_info(tmdb_id, is_movie=True):
    log.debug("Getting IMDB rating for tmdb_id = %s" % tmdb_id)

    if not tmdb_id:
        log.warn("Skipping getting data: tmdb_id is null.")
        return {}

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
    def from_ref_obj(self, ref_obj, imdb="", tmdb="", genres=None):
        new_poster = ref_obj._poster or self.model()
        new_poster.imdb = imdb
        new_poster.tmdb = tmdb
        new_poster.save()

        if genres:
            for genre in genres:
                new_poster.genres.add(genre)

        ref_obj._poster = new_poster
        ref_obj.save()
        return new_poster


class Poster(TimeStampModel):
    plot = models.TextField(blank=True, null=False, default="")
    extendedplot = models.TextField(blank=True, null=False, default="")
    genres = models.ManyToManyField("mediaviewer.Genre", blank=True, editable=False)
    actors = models.ManyToManyField("mediaviewer.Actor", blank=True, editable=False)
    writers = models.ManyToManyField("mediaviewer.Writer", blank=True, editable=False)
    directors = models.ManyToManyField(
        "mediaviewer.Director", blank=True, editable=False
    )
    episodename = models.CharField(blank=True, null=False, default="", max_length=256)
    rated = models.CharField(blank=True, null=False, default="", max_length=256)
    rating = models.CharField(blank=True, null=False, default="", max_length=32)
    tmdb = models.CharField(null=False, default="", blank=True, max_length=32)
    imdb = models.CharField(null=False, default="", blank=True, max_length=32)
    image = models.ImageField(upload_to="uploads/%Y/%m/%d/", blank=True)
    tagline = models.CharField(blank=True, null=False, default="", max_length=256)
    release_date = models.DateField(blank=True, null=True)

    objects = PosterManager()

    def __str__(self):
        if self.season is None or self.episode is None:
            return f"<Poster n:{self.short_name} i:{bool(self.image)}>"
        else:
            return f"<Poster n:{self.short_name} s:{self.season} e:{self.episode} i:{bool(self.image)}>"

    def clear(self):
        self.imdb = ""
        self.tmdb = ""
        self.plot = ""
        self.extendedplot = ""
        self.genres.clear()
        self.actors.clear()
        self.writers.clear()
        self.directors.clear()
        self.episodename = ""
        self.rated = ""
        self.rating = ""
        self.image.delete()
        self.release_date = None

    @property
    def short_name(self):
        return self.ref_obj.short_name if self.ref_obj else ""

    def __repr__(self):
        return str(self)

    @property
    def season(self):
        return getattr(self.ref_obj, "season", None)

    @property
    def episode(self):
        return getattr(self.ref_obj, "episode", None)

    @property
    def ref_obj(self):
        """
        Reference object for this Poster.

        This object will be one of a MediaFile, TV, or Movie.
        """
        if not hasattr(self, "_ref_obj"):
            # Find ref_obj through reverse relationships
            self._ref_obj = (
                getattr(self, "media_file", None)
                or getattr(self, "tv", None)
                or getattr(self, "movie", SENTINEL)
            )

        if self._ref_obj == SENTINEL:
            return None
        return self._ref_obj

    @property
    def name(self):
        return self.ref_obj.full_name if self.ref_obj else ""

    @admin.display(boolean=True, description="Image")
    def has_image(self):
        return bool(self.image)

    def display_genres(self):
        return ", ".join([x.genre for x in self.genres.all()])

    def display_actors(self):
        return ", ".join([x.name for x in self.actors.order_by("order").all()])

    def display_writers(self):
        return ", ".join([x.name for x in self.writers.all()])

    def display_directors(self):
        return ", ".join([x.name for x in self.directors.all()])

    def _get_data_from_imdb(self):
        resp = None

        if not self.tmdb:
            if self.ref_obj.is_tv() and self.ref_obj.is_media_file():
                self.tmdb = self.ref_obj.tv.poster.tmdb

            if not self.tmdb:
                if self.imdb:
                    log.debug(f"Getting data from IMDB using {self.imdb}")

                    url = f"https://api.themoviedb.org/3/find/{self.imdb}?api_key={settings.API_KEY}&external_source=imdb_id"

                    resp = getJSONData(url)

                    try:
                        if self.ref_obj.is_movie():
                            self.tmdb = resp["movie_results"][0]["id"]
                            resp = resp["movie_results"][0]
                        elif hasattr(self, "tv"):
                            self.tmdb = resp["tv_results"][0]["id"]
                            resp = resp["tv_results"][0]
                        else:
                            self.tmdb = resp["tv_episode_results"][0]["id"]
                            resp = resp["tv_episode_results"][0]
                    except Exception:
                        self.tmdb = ""
                        resp = {}

            if not self.tmdb:
                if self.ref_obj.is_movie():
                    url = f"https://api.themoviedb.org/3/search/movie?query={self.ref_obj.short_name}&api_key={settings.API_KEY}"
                else:
                    url = f"https://api.themoviedb.org/3/search/tv?query={self.ref_obj.short_name}&api_key={settings.API_KEY}"
                resp = getJSONData(url)
                if resp.get("results"):
                    self.tmdb = resp["results"][0]["id"]
                    resp = resp["results"][0]

        if self.tmdb:
            if not self.ref_obj.is_movie():
                log.debug(f"Getting TV data from TVDB using {self.tmdb}")

                url = f"https://api.themoviedb.org/3/tv/{self.tmdb}?language=en-US&api_key={settings.API_KEY}"

                try:
                    resp = getJSONData(url)
                except Exception:
                    log.debug(f"Got bad tmdb_id={self.tmdb}. Revert to parent tmdb")
                    self.tmdb = self.ref_obj.media.poster.tmdb if self.ref_obj else None

                    if self.tmdb:
                        url = f"https://api.themoviedb.org/3/tv/{self.tmdb}?language=en-US&api_key={settings.API_KEY}"
                        try:
                            resp = getJSONData(url)
                        except Exception:
                            resp = None
                    else:
                        resp = None
            else:
                log.debug(f"Getting Movie data from TVDB using {self.tmdb}")

                url = f"https://api.themoviedb.org/3/movie/{self.tmdb}?language=en-US&api_key={settings.API_KEY}"

                try:
                    resp = getJSONData(url)
                except Exception:
                    log.debug(f"Got bad tmdb_id={self.tmdb}. Reverting to null")
                    self.tmdb = ""
                    resp = None

        if resp:
            resp["url"] = url

        return resp

    def populate_data(self, clear=False):
        log.debug("Attempt to get data from IMDB")

        if clear:
            self.clear()

        data = self._get_data_from_imdb()

        if not data:
            return None

        if not self.tmdb and "id" in data:
            self.tmdb = data["id"]

        self._cast_and_crew()
        self._store_extended_info()
        self._store_plot(data)
        self._store_genres(data)
        self._store_rated(data)

        if not self.ref_obj.is_movie():
            self._tmdb_episode_info()
        else:
            self._store_release_date(data)

        poster_url = (
            getattr(self, "poster_url", None)
            or data.get("Poster")
            or data.get("poster_path")
        )
        poster_name = poster_url.rpartition("/")[-1] if poster_url else None

        if poster_name:
            r = requests.get(
                "{url}{poster_size}{path}".format(
                    url=tvdbConfig.url,
                    poster_size=tvdbConfig.poster_size,
                    path=poster_url,
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
        else:
            self.image.delete()

        self.save()

        return data

    def _tmdb_episode_info(self):
        if not self.tmdb:
            return None

        tvinfo = getTVDBEpisodeInfo(self.tmdb, self.season, self.episode)

        if tvinfo:
            self.poster_url = (
                tvinfo.get("still_path")
                or tvinfo.get("poster_path")
                or getattr(self, "poster_url", None)
            )
            self.extendedplot = tvinfo.get("overview", "")
            self.episodename = tvinfo.get("name")
            self.tmdb = tvinfo.get("id", self.tmdb) or ""

            if hasattr(self, "tv"):
                if release_date_str := tvinfo.get("first_air_date"):
                    self.release_date = date.fromisoformat(release_date_str)
                else:
                    self.release_date = None
            else:
                if release_date_str := tvinfo.get("air_date"):
                    self.release_date = date.fromisoformat(release_date_str)
                else:
                    self.release_date = None

        if self.ref_obj.is_media_file():
            self.ref_obj.populate_display_name()
            self.ref_obj.save()

    def _store_plot(self, imdb_data):
        plot = (
            imdb_data.get("Plot")
            or imdb_data.get("overview")
            or "results" in imdb_data
            and imdb_data["results"]
            and imdb_data["results"][0].get("overview")
        )
        self.plot = plot if plot and plot != "undefined" else ""

    def _store_extended_info(self):
        try:
            extended_info = _get_extended_info(
                self.tmdb, is_movie=self.ref_obj.is_movie()
            )
        except Exception as e:
            log.warning("Extended info not found")
            log.warning(e)
            return

        self._store_rating(extended_info)
        self._store_tagline(extended_info)

    def _store_tagline(self, extended_info):
        tagline = extended_info.get("tagline")
        self.tagline = tagline if tagline and tagline != "undefined" else ""

    def _store_rating(self, extended_info):
        rating = extended_info.get("imdbRating") or extended_info.get("vote_average")
        self.rating = rating if rating and rating != "undefined" else ""

    def _store_rated(self, imdb_data):
        rated = imdb_data.get("Rated")
        self.rated = rated if rated and rated != "undefined" else ""

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

    def _store_release_date(self, imdb_data):
        if release_date_str := imdb_data.get("release_date"):
            self.release_date = date.fromisoformat(release_date_str)
        else:
            self.release_date = None
