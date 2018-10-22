import time
import os
from mediaviewer.log import log
from mysite.settings import (API_KEY,
                             OMDBAPI_KEY,
                             IMAGE_PATH,
                             REQUEST_TIMEOUT,
                             )
import requests


def getJSONData(url):
    try:
        url = url.replace(' ', '+')
        log.info('Getting json from %s' % (url,))
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        log.debug('Got %s' % (data,))

        if 'X-RateLimit-Remaining' in resp.headers:
            remaining = int(resp.headers['X-RateLimit-Remaining'])
            limit = int(resp.headers.get('X-RateLimit-Limit', '40'))

            if remaining < .1 * limit:
                log.warning('90%% of the rate limit has been used. '
                            'Sleeping for 1 second')
                time.sleep(1)

        return data
    except Exception, e:
        log.error(str(e), exc_info=True)


class TVDBConfiguration(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TVDBConfiguration, cls).__new__(
                    cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        log.debug('Getting tvdb config')
        try:
            data = self._getTVDBConfiguration()
            self.url = data['images']['secure_base_url']
            self.poster_size = 'w500'
            self.still_size = data['images']['still_sizes'][-1]
            self.connected = True

            genres = self._getTVDBGenres()
            if not genres:
                raise Exception('No genres returned')

            self.genres = genres
            log.debug('tvdb values set successfully')
        except Exception, e:
            self.url = ''
            self.poster_size = ''
            self.still_size = ''
            self.connected = False
            self.genres = {}
            log.error(str(e), exc_info=True)
            log.debug('Failed to set tvdb values')

    def _getTVDBConfiguration(self):
        url = 'https://api.themoviedb.org/3/configuration?api_key=%s' % (API_KEY,)
        return getJSONData(url)

    def _getTVDBGenres(self):
        data = {}

        url = 'https://api.themoviedb.org/3/genre/tv/list?api_key=%s' % (API_KEY,)
        resp = getJSONData(url)
        genres = resp['genres']
        for genre in genres:
            data[genre['id']] = genre['name']

        url = 'https://api.themoviedb.org/3/genre/movie/list?api_key=%s' % (API_KEY,)
        resp = getJSONData(url)
        genres = resp['genres']
        for genre in genres:
            data[genre['id']] = genre['name']

        return data


tvdbConfig = TVDBConfiguration()


def searchTVDBByName(name):
    if not tvdbConfig.connected:
        return {}

    url = 'https://api.themoviedb.org/3/search/tv?query=%s&api_key=%s' % (name, API_KEY)
    return getJSONData(url)


def getTVDBEpisodeInfo(tvdb_id, season, episode):
    log.debug('Getting tvdb episode info for %s, season: %s, episode: %s' % (tvdb_id, season, episode))
    if not tvdbConfig.connected:
        return {}

    url = 'https://api.themoviedb.org/3/tv/%s/season/%s/episode/%s?api_key=%s' % (tvdb_id, season, episode, API_KEY)
    return getJSONData(url)


def saveImageToDisk(path, imgName):
    log.debug('Getting image from %s' % (path,))
    if imgName:
        exists = os.path.isfile(IMAGE_PATH + imgName)
        if not exists:
            r = requests.get('{url}{poster_size}{path}'.format(
                url=tvdbConfig.url,
                poster_size=tvdbConfig.poster_size,
                path=path),
                stream=True,
                timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            if r.status_code == 200:
                with open(IMAGE_PATH + imgName, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
        else:
            log.debug('File already exists. Skipping')
    else:
        log.info('No image name given. Skipping')


def getDataFromIMDB(ref_obj):
    if ref_obj.isPath:
        files = ref_obj.files()
        refFile = files and files[0]
    else:
        refFile = ref_obj

    if not refFile.imdb_id and refFile.path.imdb_id:
        refFile.imdb_id = refFile.path.imdb_id

    if refFile.imdb_id and refFile.imdb_id != 'None':
        return _getDataFromIMDBByID(refFile.imdb_id, isMovie=refFile.isMovie())
    else:
        return _getDataFromIMDBBySearchString(
                refFile.searchString(),
                isMovie=refFile.isMovie())


def getDataFromIMDBByPath(refPath):
    if refPath.imdb_id:
        return _getDataFromIMDBByID(refPath.imdb_id, isMovie=refPath.isMovie())
    else:
        files = refPath.files()
        refFile = files and files[0]

        if not refFile:
            log.warning('No files found associated with path. Skipping')
            return None
        else:
            log.debug('Using %s for refFile' % (refFile,))

        return getDataFromIMDB(refFile)


# TODO: Test me!!!!
def _getDataFromIMDBByID(imdb_id, isMovie=True):
    log.debug('Getting data from IMDB using %s' % (imdb_id,))

    url = 'https://api.themoviedb.org/3/find/%s?api_key=%s&external_source=imdb_id' % (imdb_id, API_KEY)
    resp = getJSONData(url)

    if resp:
        if not isMovie:
            tmdb_id = resp.get('tv_results')[0]['id']
            url = 'https://api.themoviedb.org/3/tv/%s?api_key=%s' % (tmdb_id, API_KEY)
        else:
            tmdb_id = resp.get('movie_results')[0]['id']
            url = 'https://api.themoviedb.org/3/movie/%s?api_key=%s' % (tmdb_id, API_KEY)

        data = getJSONData(url)

        if data:
            data['url'] = url
        else:
            return None
        return data


def _getDataFromIMDBBySearchString(searchString, isMovie=True):
    log.debug('Getting data from IMDB using %s' % (searchString,))

    if not isMovie:
        url = 'https://api.themoviedb.org/3/search/tv?query=%s&api_key=%s' % (searchString, API_KEY)
    else:
        url = 'https://api.themoviedb.org/3/search/movie?query=%s&api_key=%s' % (searchString, API_KEY)

    data = getJSONData(url)
    data = (data['results'][0]
            if data and
            data.get('results') and
            data.get('results')[0] else None)
    if data:
        data['url'] = url
    else:
        return None
    return data


def getCastData(tmdb_id, season=None, episode=None, isMovie=True):
    log.debug('Getting data from TVDb using %s' % (tmdb_id,))

    if not isMovie:
        if episode and season:
            url = 'https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season}/episode/{episode}/credits?api_key={api_key}'.format(
                    season=season,
                    episode=episode,
                    tmdb_id=tmdb_id,
                    api_key=API_KEY)
        else:
            url = 'https://api.themoviedb.org/3/tv/{tmdb_id}/credits?api_key={api_key}'.format(
                    tmdb_id=tmdb_id,
                    api_key=API_KEY)
    else:
        url = 'https://api.themoviedb.org/3/movie/{tmdb_id}/credits?api_key={api_key}'.format(
                tmdb_id=tmdb_id,
                api_key=API_KEY)

    return getJSONData(url)


def getRating(tmdb_id, isMovie=True):
    log.debug('Getting IMDB rating for tmdb_id = %s' % tmdb_id)

    if not isMovie:
        url = 'https://api.themoviedb.org/3/tv/%s/external_ids?api_key=%s' % (tmdb_id, API_KEY)
    else:
        url = 'https://api.themoviedb.org/3/movie/%s?api_key=%s' % (tmdb_id, API_KEY)

    data = getJSONData(url)
    imdb_id = data and data.get('imdb_id')

    if imdb_id and OMDBAPI_KEY:
        url = 'http://www.omdbapi.com/?i=%s' % imdb_id

        try:
            data = getJSONData(url)
            return data['imdbRating']
        except Exception as e:
            log.error('Received error trying to get imdbRating')
            log.error(e)
