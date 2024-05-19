import os
import time

import requests
from django.conf import settings

from mediaviewer.log import log


def getJSONData(url):
    try:
        url = url.replace(" ", "+")
        log.info("Getting json from %s" % (url,))
        resp = requests.get(url, timeout=settings.REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        log.debug("Got %s" % (data,))

        if "X-RateLimit-Remaining" in resp.headers:
            remaining = int(resp.headers["X-RateLimit-Remaining"])
            limit = int(resp.headers.get("X-RateLimit-Limit", "40"))

            if remaining < 0.1 * limit:
                log.warning(
                    "90%% of the rate limit has been used. Sleeping for 1 second"
                )
                time.sleep(1)

        return data
    except Exception as e:
        log.error(str(e), exc_info=True)
        raise


class TVDBConfiguration:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TVDBConfiguration, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        log.debug("Getting tvdb config")
        try:
            data = self._getTVDBConfiguration()
            self.url = data["images"]["secure_base_url"]
            self.poster_size = "w500"
            self.still_size = data["images"]["still_sizes"][-1]
            self.connected = True

            genres = self._getTVDBGenres()
            if not genres:
                raise Exception("No genres returned")

            self.genres = genres
            log.debug("tvdb values set successfully")
        except Exception as e:
            self.url = ""
            self.poster_size = ""
            self.still_size = ""
            self.connected = False
            self.genres = {}
            log.error(str(e), exc_info=True)
            log.debug("Failed to set tvdb values")

    def _getTVDBConfiguration(self):
        url = "https://api.themoviedb.org/3/configuration?api_key={}".format(
            settings.API_KEY
        )
        return getJSONData(url)

    def _getTVDBGenres(self):
        data = {}

        url = "https://api.themoviedb.org/3/genre/tv/list?api_key={}".format(
            settings.API_KEY
        )
        resp = getJSONData(url)
        genres = resp["genres"]
        for genre in genres:
            data[genre["id"]] = genre["name"]

        url = "https://api.themoviedb.org/3/genre/movie/list?api_key={}".format(
            settings.API_KEY
        )
        resp = getJSONData(url)
        genres = resp["genres"]
        for genre in genres:
            data[genre["id"]] = genre["name"]

        return data


tvdbConfig = TVDBConfiguration()


def searchTVDBByName(name):
    if not tvdbConfig.connected:
        return {}

    url = (
        "https://api.themoviedb.org/3/search/tv?query={name}&api_key={api_key}".format(
            name=name, api_key=settings.API_KEY
        )
    )
    return getJSONData(url)


def getTVDBEpisodeInfo(tvdb_id, season, episode):
    if not tvdbConfig.connected:
        log.debug(
            f"Could not get episode specific information. tvdbConfig.connected={tvdbConfig.connected}"
        )
        return {}

    log.debug(
        f"Getting tvdb episode info for {tvdb_id}, "
        f"season: {season}, episode: {episode}"
    )

    urls = []

    if episode and season:
        urls.append(
            f"https://api.themoviedb.org/3/tv/{tvdb_id}/season/{season}/episode/{episode}?api_key={settings.API_KEY}"
        )

    if season:
        urls.append(
            f"https://api.themoviedb.org/3/tv/{tvdb_id}/season/{season}?api_key={settings.API_KEY}"
        )

    urls.append(f"https://api.themoviedb.org/3/tv/{tvdb_id}?api_key={settings.API_KEY}")

    resp = {}
    for url in urls:
        try:
            resp = getJSONData(url)
        except Exception as e:
            log.debug(e)
            continue

        if resp:
            break
    return resp


def saveImageToDisk(path, imgName):
    log.debug("Getting image from %s" % (path,))
    if imgName:
        exists = os.path.isfile(settings.IMAGE_PATH + imgName)
        if not exists:
            r = requests.get(
                "{url}{poster_size}{path}".format(
                    url=tvdbConfig.url, poster_size=tvdbConfig.poster_size, path=path
                ),
                stream=True,
                timeout=settings.REQUEST_TIMEOUT,
            )
            r.raise_for_status()
            if r.status_code == 200:
                with open(settings.IMAGE_PATH + imgName, "wb") as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
        else:
            log.debug("File already exists. Skipping")
    else:
        log.info("No image name given. Skipping")


def getDataFromIMDB(ref_obj):
    if ref_obj.isPath:
        files = ref_obj.files()
        refFile = files and files[0]
    else:
        refFile = ref_obj

    if not refFile.imdb_id and refFile.path.imdb_id:
        refFile.imdb_id = refFile.path.imdb_id

    if refFile.imdb_id and refFile.imdb_id != "None":
        return _getDataFromIMDBByID(refFile.imdb_id, isMovie=refFile.isMovie())
    else:
        return _getDataFromIMDBBySearchString(
            refFile.searchString(), isMovie=refFile.isMovie()
        )


def getDataFromIMDBByPath(refPath):
    if refPath.imdb_id:
        return _getDataFromIMDBByID(refPath.imdb_id, isMovie=refPath.isMovie())
    else:
        files = refPath.files()
        refFile = files and files[0]

        if not refFile:
            log.warning("No files found associated with path. Skipping")
            return None
        else:
            log.debug("Using %s for refFile" % (refFile,))

        return getDataFromIMDB(refFile)


# TODO: Test me!!!!
def _getDataFromIMDBByID(imdb_id, isMovie=True):
    log.debug("Getting data from IMDB using %s" % (imdb_id,))

    url = "https://api.themoviedb.org/3/find/{imdb_id}?api_key={api_key}&external_source=imdb_id".format(  # noqa
        imdb_id=imdb_id, api_key=settings.API_KEY
    )
    resp = getJSONData(url)

    if resp:
        if not isMovie:
            if resp.get("tv_results"):
                tmdb_id = resp.get("tv_results")[0]["id"]
                url = "https://api.themoviedb.org/3/tv/{tmdb_id}?api_key={api_key}".format(
                    tmdb_id=tmdb_id, api_key=settings.API_KEY
                )
            elif resp.get("tv_episode_results"):
                tmdb_id = resp.get("tv_episode_results")[0]["id"]
                url = "https://api.themoviedb.org/3/tv/{tmdb_id}?api_key={api_key}".format(
                    tmdb_id=tmdb_id, api_key=settings.API_KEY
                )
        else:
            tmdb_id = resp.get("movie_results")[0]["id"]
            url = "https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={api_key}".format(  # noqa
                tmdb_id=tmdb_id, api_key=settings.API_KEY
            )

        if tmdb_id:
            data = getJSONData(url)
        else:
            data = None

        if data:
            data["url"] = url
        else:
            return None
        return data


def _getDataFromIMDBBySearchString(searchString, isMovie=True):
    log.debug("Getting data from IMDB using %s" % (searchString,))

    if not isMovie:
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


def getCastData(tmdb_id, season=None, episode=None, isMovie=True):
    log.info("Getting data from TVDb using %s" % (tmdb_id,))

    if not tmdb_id:
        log.warn("Skipping getting data: tmdb_id is null")
        return {}

    if not isMovie:
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


def getExtendedInfo(tmdb_id, isMovie=True):
    log.debug("Getting IMDB rating for tmdb_id = %s" % tmdb_id)

    if not isMovie:
        url = "https://api.themoviedb.org/3/tv/{tmdb_id}/external_ids?api_key={api_key}".format(  # noqa
            tmdb_id=tmdb_id, api_key=settings.API_KEY
        )
    else:
        url = "https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={api_key}".format(  # noqa
            tmdb_id=tmdb_id, api_key=settings.API_KEY
        )

    data = getJSONData(url)
    return data
