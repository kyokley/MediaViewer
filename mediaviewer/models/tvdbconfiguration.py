import os, urllib2, json
from mediaviewer.log import log
from site.settings import (API_KEY,
                             OMDB_URL,
                             OMDB_ID_URL,
                             OMDB_URL_TAIL,
                             IMAGE_PATH,
                             )

def getJSONData(url):
    try:
        url = url.replace(' ','+')
        log.info('Getting json from %s' % (url,))
        resp = urllib2.urlopen(url)
        data = json.load(resp)
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
            image = urllib2.urlopen(url).read()
            output = open(IMAGE_PATH + imgName, 'wb')
            output.write(image)
            output.close()
        else:
            log.debug('File already exists. Skipping')
    else:
        log.info('No image name given. Skipping')

def getDataFromIMDB(refFile, useExtendedPlot=False):
    log.debug('Getting data from IMDB using %s' % (refFile,))
    if refFile.imdb_id and refFile.imdb_id != 'None':
        url = OMDB_ID_URL + refFile.imdb_id
    else:
        url = OMDB_URL + refFile.searchString()

    if useExtendedPlot:
        url = url + OMDB_URL_TAIL

    data = getJSONData(url)
    data['url'] = url
    return data

def assignDataToPoster(data, poster, onlyExtendedPlot=False, foundNone=False):
    if not foundNone:
        if not onlyExtendedPlot:
            poster.plot = (not data.get('Plot', None) or data.get('Plot', None) == 'undefined') and 'Plot not found' or data.get('Plot', None)
            poster.genre = (not data.get('Genre', None) or data.get('Genre', None) == 'undefined') and 'Genre not found' or data.get('Genre', None)
            poster.actors = (not data.get('Actors', None) or data.get('Actors', None) == 'undefined') and 'Actors not found' or data.get('Actors', None)
            poster.writer = (not data.get('Writer', None) or data.get('Writer', None) == 'undefined') and 'Writer not found' or data.get('Writer', None)
            poster.director = (not data.get('Director', None) or data.get('Director', None) == 'undefined') and 'Director not found' or data.get('Director', None)
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

