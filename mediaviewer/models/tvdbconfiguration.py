import os
from mediaviewer.log import log
from mysite.settings import (API_KEY,
                             OMDB_URL,
                             OMDB_ID_URL,
                             OMDB_URL_TAIL,
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
            self.poster_size = data['images']['poster_sizes'][-1]
            self.still_size = data['images']['still_sizes'][-1]
            self.connected = True
            log.debug('tvdb values set successfully')
        except Exception, e:
            self.url = ''
            self.poster_size = ''
            self.still_size = ''
            self.connected = False
            log.error(str(e), exc_info=True)
            log.debug('Failed to set tvdb values')

    def _getTVDBConfiguration(self):
        url = 'https://api.themoviedb.org/3/configuration?api_key=%s' % (API_KEY,)
        return getJSONData(url)
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

def saveImageToDisk(url, imgName):
    log.debug('Getting image from %s' % (url,))
    if imgName:
        exists = os.path.isfile(IMAGE_PATH + imgName)
        if not exists:
            r = requests.get(url, stream=True, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            if r.status_code == 200:
                with open(IMAGE_PATH + imgName, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
        else:
            log.debug('File already exists. Skipping')
    else:
        log.info('No image name given. Skipping')

def getDataFromIMDB(refFile, useExtendedPlot=False):
    if not refFile.imdb_id and refFile.path.imdb_id:
        refFile.imdb_id = refFile.path.imdb_id

    if refFile.imdb_id and refFile.imdb_id != 'None':
        return _getDataFromIMDBByID(refFile.imdb_id, useExtendedPlot=useExtendedPlot)
    else:
        return _getDataFromIMDBBySearchString(refFile.searchString(), useExtendedPlot=useExtendedPlot)

def getDataFromIMDBByPath(refPath, useExtendedPlot=False):
    if refPath.imdb_id:
        return _getDataFromIMDBByID(refPath.imdb_id, useExtendedPlot=useExtendedPlot)
    else:
        files = refPath.files()
        refFile = files and files[0]

        if not refFile:
            log.warning('No files found associated with path. Skipping')
            return None
        else:
            log.debug('Using %s for refFile' % (refFile,))

        return getDataFromIMDB(refFile, useExtendedPlot=useExtendedPlot)

def _getDataFromIMDBByID(imdb_id, useExtendedPlot=False):
    log.debug('Getting data from IMDB using %s' % (imdb_id,))
    url = OMDB_ID_URL + imdb_id

    if useExtendedPlot:
        url = url + OMDB_URL_TAIL

    data = getJSONData(url)
    if data:
        data['url'] = url
    else:
        return None
    return data

def _getDataFromIMDBBySearchString(searchString, useExtendedPlot=False):
    log.debug('Getting data from IMDB using %s' % (searchString,))
    url = OMDB_URL + searchString

    if useExtendedPlot:
        url = url + OMDB_URL_TAIL

    data = getJSONData(url)
    if data:
        data['url'] = url
    else:
        return None
    return data

def assignDataToPoster(data, poster, onlyExtendedPlot=False, foundNone=False):
    if not foundNone:
        if not onlyExtendedPlot:
            plot = data.get('Plot')
            poster.plot = (not plot or plot == 'undefined') and 'Plot not found' or plot
            genre = data.get('Genre', None)
            poster.genre = (not genre or genre == 'undefined') and 'Genre not found' or genre
            actors = data.get('Actors')
            poster.actors = (not actors or actors == 'undefined') and 'Actors not found' or actors
            writer = data.get('Writer')
            poster.writer = (not writer or writer == 'undefined') and 'Writer not found' or writer
            director = data.get('Director')
            poster.director = (not director or director == 'undefined') and 'Director not found' or director
            rating = data.get('imdbRating')
            poster.rating = rating != 'undefined' and rating or None
            rated = data.get('Rated')
            poster.rated = rated != 'undefined' and rated or None
        else:
            poster.extendedplot = (not data.get('Plot', None) or data.get('Plot', None) == 'undefined') and 'Plot not found' or data.get('Plot', None)
    else:
        log.debug('Nullifying poster values')
        poster.plot = 'Plot not found'
        poster.genre = 'Genre not found'
        poster.actors = 'Actors not found'
        poster.writer = 'Writer not found'
        poster.director = 'Director not found'
        poster.extendedplot = 'Extended plot not found'
