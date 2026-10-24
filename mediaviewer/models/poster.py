"""
Re-implementation of PosterFile
"""

from datetime import date
from io import BytesIO
from urllib.parse import quote_plus

import requests
from django.conf import settings
from django.contrib import admin
from django.contrib.sites.models import Site
from django.core.files.images import ImageFile
from django.db import DatabaseError, models

from mediaviewer.log import log

from ..thetvdb import _normalize
from .actor import Actor
from .core import TimeStampModel
from .director import Director
from .genre import Genre
from .tvdbconfiguration import getJSONData, getTVDBEpisodeInfo, tvdbConfig
from .writer import Writer

SENTINEL = object()
POSTER_PATH_BASE_URL = "https://image.tmdb.org/t/p/original/"


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


def _valid_tmdb_id(value):
    return (
        isinstance(value, (str, int))
        and not isinstance(value, bool)
        and bool(str(value))
    )


def _get_cast_data(tmdb_id, season=None, episode=None, is_movie=True):
    log.info("Getting data from TVDb using %s" % (tmdb_id,))
    if not tmdb_id:
        log.warn("Skipping getting data: tmdb_id is null.")
        return {}

    urls = []

    if not is_movie:
        if episode is not None and season is not None:
            urls.append(
                f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season}/episode/{episode}/credits?api_key={settings.API_KEY}"
            )

        if season is not None:
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

    def external_url(self):
        if not self.image:
            return ""

        if settings.OG_BASE_URL:
            return f"{settings.OG_BASE_URL}/{self.image.url}"
        else:
            current_site = Site.objects.get_current()
            return f"{settings.HTTP_PROTOCOL}://{current_site.domain}{self.image.url}"

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

        if self.ref_obj.is_media_file() and self.ref_obj.is_tv():
            return self._populate_tv_episode_data()

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
            or f"{POSTER_PATH_BASE_URL}{data.get('poster_path')}"
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

    def _get_tv_series_tmdb_id(self, tv):
        parent_poster = tv._poster if tv._poster_id else None
        if parent_poster and parent_poster.tmdb:
            return str(parent_poster.tmdb), parent_poster

        if parent_poster and parent_poster.imdb:
            url = (
                f"https://api.themoviedb.org/3/find/{parent_poster.imdb}"
                f"?api_key={settings.API_KEY}&external_source=imdb_id"
            )
            try:
                data = getJSONData(url)
                results = data.get("tv_results") if isinstance(data, dict) else None
                if (
                    isinstance(results, list)
                    and results
                    and isinstance(results[0], dict)
                    and _valid_tmdb_id(results[0].get("id"))
                ):
                    tmdb_id = str(results[0]["id"])
                    if parent_poster:
                        parent_poster.tmdb = tmdb_id
                        parent_poster.save(update_fields=["tmdb"])
                    return tmdb_id, parent_poster
            except DatabaseError:
                raise
            except Exception as e:
                log.debug(e)

        if parent_poster is None:
            parent_poster = Poster.objects.from_ref_obj(tv)

        try:
            url = ("https://api.themoviedb.org/3/search/tv?query={}&api_key={}").format(
                quote_plus(tv.name), settings.API_KEY
            )
            data = getJSONData(url)
            results = data.get("results") if isinstance(data, dict) else None
            target_name = _normalize(tv.name)
            matches = []
            if isinstance(results, list) and target_name:
                for result in results:
                    if not isinstance(result, dict):
                        continue
                    names = (result.get("name"), result.get("original_name"))
                    if any(
                        isinstance(name, str) and _normalize(name) == target_name
                        for name in names
                    ):
                        matches.append(result)
            if len(matches) == 1 and _valid_tmdb_id(matches[0].get("id")):
                tmdb_id = str(matches[0]["id"])
                parent_poster.tmdb = tmdb_id
                parent_poster.save(update_fields=["tmdb"])
                return tmdb_id, parent_poster
        except DatabaseError:
            raise
        except Exception as e:
            log.debug(e)

        return "", parent_poster

    def _populate_tv_episode_data(self):
        media_file = self.ref_obj
        if media_file.season is None or media_file.episode is None:
            return None

        series_id, _ = self._get_tv_series_tmdb_id(media_file.tv)
        if not series_id:
            return None

        try:
            tvinfo = getTVDBEpisodeInfo(
                series_id, media_file.season, media_file.episode
            )
        except DatabaseError:
            raise
        except Exception as e:
            log.warning("Episode metadata not found")
            log.warning(e)
            return None

        if not isinstance(tvinfo, dict) or not tvinfo:
            return None

        changed_fields = []
        title = tvinfo.get("name")
        if isinstance(title, str) and title.strip():
            self.episodename = title
            changed_fields.append("episodename")
        overview = tvinfo.get("overview")
        if isinstance(overview, str):
            self.extendedplot = overview
            changed_fields.append("extendedplot")
        release_date = tvinfo.get("air_date")
        if isinstance(release_date, str) and release_date:
            try:
                self.release_date = date.fromisoformat(release_date)
                changed_fields.append("release_date")
            except ValueError:
                log.debug("Invalid episode air date: %s", release_date)
        if tvinfo.get("id") is not None:
            self.tmdb = str(tvinfo["id"])
            changed_fields.append("tmdb")
        if changed_fields:
            self.save(update_fields=changed_fields)

        if "episodename" in changed_fields:
            media_file.populate_display_name()
            media_file.save(update_fields=["display_name"])

        self._populate_tv_episode_optional_data(tvinfo, series_id)
        self._populate_tv_series_details(series_id)
        return tvinfo

    def _populate_tv_series_details(self, series_id):
        url = (
            f"https://api.themoviedb.org/3/tv/{series_id}"
            f"?language=en-US&api_key={settings.API_KEY}"
        )
        try:
            data = getJSONData(url)
            if not isinstance(data, dict):
                return
            changed_fields = []
            if data.get("Plot") or data.get("overview"):
                self._store_plot(data)
                changed_fields.append("plot")
            if "Rated" in data:
                self._store_rated(data)
                changed_fields.append("rated")
            if changed_fields:
                self.save(update_fields=changed_fields)
            if data.get("genres") or data.get("genre_ids") or data.get("results"):
                try:
                    self._store_genres(data)
                except DatabaseError:
                    raise
                except Exception as e:
                    log.debug(e)
        except DatabaseError:
            raise
        except Exception as e:
            log.debug(e)

    def _populate_tv_episode_optional_data(self, tvinfo, series_id):
        image_path = tvinfo.get("still_path") or tvinfo.get("poster_path")
        if isinstance(image_path, str) and image_path:
            try:
                if image_path.startswith(("http://", "https://")):
                    image_url = image_path
                else:
                    image_size = (
                        tvdbConfig.still_size
                        if tvinfo.get("still_path")
                        else tvdbConfig.poster_size
                    )
                    image_url = f"{tvdbConfig.url}{image_size}{image_path}"
                response = requests.get(
                    image_url, stream=True, timeout=settings.REQUEST_TIMEOUT
                )
                response.raise_for_status()
                if response.status_code == 200:
                    image_data = BytesIO()
                    for chunk in response.iter_content(1024):
                        image_data.write(chunk)
                    image_data.seek(0)
                    self.image = ImageFile(
                        image_data, name=image_path.rpartition("/")[-1]
                    )
                    self.save(update_fields=["image"])
            except DatabaseError:
                raise
            except Exception as e:
                log.warning("Episode image not found")
                log.debug(e)

        try:
            extended_info = _get_extended_info(series_id, is_movie=False)
            if isinstance(extended_info, dict):
                changed_fields = []
                rating = extended_info.get("imdbRating") or extended_info.get(
                    "vote_average"
                )
                if isinstance(rating, (str, int, float)) and rating != "undefined":
                    self.rating = str(rating)
                    changed_fields.append("rating")
                tagline = extended_info.get("tagline")
                if isinstance(tagline, str) and tagline and tagline != "undefined":
                    self.tagline = tagline
                    changed_fields.append("tagline")
                if changed_fields:
                    self.save(update_fields=changed_fields)
        except DatabaseError:
            raise
        except Exception as e:
            log.debug(e)

        try:
            cast_and_crew = _get_cast_data(
                series_id,
                season=self.season,
                episode=self.episode,
                is_movie=False,
            )
            if not isinstance(cast_and_crew, dict):
                return
            for actor in cast_and_crew.get("cast", []):
                if isinstance(actor, dict) and actor.get("name"):
                    actor_obj = Actor.objects.create(
                        name=actor["name"], order=actor.get("order")
                    )
                    self.actors.add(actor_obj)
            for job in cast_and_crew.get("crew", []):
                if not isinstance(job, dict) or not job.get("name"):
                    continue
                if job.get("job") == "Writer":
                    self.writers.add(Writer.objects.create(name=job["name"]))
                elif job.get("job") == "Director":
                    self.directors.add(Director.objects.create(name=job["name"]))
        except DatabaseError:
            raise
        except Exception as e:
            log.debug(e)

    def _tmdb_episode_info(self):
        if not self.tmdb:
            return None

        tvinfo = getTVDBEpisodeInfo(self.tmdb, self.season, self.episode)

        if tvinfo:
            self.poster_url = (
                tvinfo.get("still_path")
                or f"{POSTER_PATH_BASE_URL}{tvinfo.get('poster_path')}"
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
