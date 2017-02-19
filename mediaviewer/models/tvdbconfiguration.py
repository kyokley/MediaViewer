import os
from mediaviewer.log import log
from mysite.settings import (API_KEY,
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
        return data
    except Exception, e:
        log.error(str(e), exc_info=True)

#TODO: Add tvdb config to database and update values weekly
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
            #self.poster_size = data['images']['poster_sizes'][-1]
            self.poster_size = 'w500'
            self.still_size = data['images']['still_sizes'][-1]
            self.connected = True
            self.genres = self._getTVDBGenres()
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
            #r = requests.get(url, stream=True, timeout=REQUEST_TIMEOUT)
            r = requests.get('{url}{poster_size}{path}'.format(url=tvdbConfig.url,
                                                               poster_size=tvdbConfig.poster_size,
                                                               path=path), stream=True, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            if r.status_code == 200:
                with open(IMAGE_PATH + imgName, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
        else:
            log.debug('File already exists. Skipping')
    else:
        log.info('No image name given. Skipping')

def getDataFromIMDB(ref_obj, useExtendedPlot=False):
    if ref_obj.isPath:
        files = ref_obj.files()
        refFile = files and files[0]
    else:
        refFile = ref_obj

    if not refFile.imdb_id and refFile.path.imdb_id:
        refFile.imdb_id = refFile.path.imdb_id

    if refFile.imdb_id and refFile.imdb_id != 'None':
        return _getDataFromIMDBByID(refFile.imdb_id, useExtendedPlot=useExtendedPlot, isMovie=refFile.isMovie())
    else:
        return _getDataFromIMDBBySearchString(refFile.searchString(), useExtendedPlot=useExtendedPlot, isMovie=refFile.isMovie())

def getDataFromIMDBByPath(refPath, useExtendedPlot=False):
    if refPath.imdb_id:
        return _getDataFromIMDBByID(refPath.imdb_id, useExtendedPlot=useExtendedPlot, isMovie=refPath.isMovie())
    else:
        files = refPath.files()
        refFile = files and files[0]

        if not refFile:
            log.warning('No files found associated with path. Skipping')
            return None
        else:
            log.debug('Using %s for refFile' % (refFile,))

        return getDataFromIMDB(refFile, useExtendedPlot=useExtendedPlot)

def _getDataFromIMDBByID(imdb_id, useExtendedPlot=False, isMovie=True):
    log.debug('Getting data from IMDB using %s' % (imdb_id,))

    url = 'https://api.themoviedb.org/3/find/%s?api_key=%s&external_source=imdb_id' % (imdb_id, API_KEY)
    resp = getJSONData(url)

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

def _getDataFromIMDBBySearchString(searchString, useExtendedPlot=False, isMovie=True):
    log.debug('Getting data from IMDB using %s' % (searchString,))

    if not isMovie:
        url = 'https://api.themoviedb.org/3/search/tv?query=%s&api_key=%s' % (searchString, API_KEY)
    else:
        url = 'https://api.themoviedb.org/3/search/movie?query=%s&api_key=%s' % (searchString, API_KEY)

    data = getJSONData(url)
    if data:
        data['url'] = url
    else:
        return None
    return data
