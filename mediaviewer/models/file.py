import re
import time
from django.db import models
from mediaviewer.models.posterfile import PosterFile
from mediaviewer.models.error import Error
from mediaviewer.models.usercomment import UserComment
from mediaviewer.models.filenamescrapeformat import FilenameScrapeFormat
from mediaviewer.models.genre import Genre
from datetime import datetime as dateObj
from django.utils.timezone import utc

from mysite.settings import (WAITER_HEAD,
                             LOCAL_WAITER_IP_FORMAT_MOVIES,
                             LOCAL_WAITER_IP_FORMAT_TVSHOWS,
                             BANGUP_WAITER_IP_FORMAT_MOVIES,
                             BANGUP_WAITER_IP_FORMAT_TVSHOWS,
                             )
from mediaviewer.models.usersettings import (LOCAL_IP,
                                             BANGUP_IP)

from mediaviewer.log import log

yearRegex = re.compile('20[01]\d.*$')
dvdRegex = re.compile('[A-Z]{2,}.*$')
formatRegex = re.compile('\b(xvid|avi|XVID|AVI)+\b')
punctuationRegex = re.compile('[^a-zA-Z0-9]+')


class File(models.Model):
    path = models.ForeignKey('mediaviewer.Path',
                             null=True,
                             db_column='pathid',
                             blank=True,
                             on_delete=models.CASCADE)
    filename = models.TextField(blank=True)
    skip = models.BooleanField(blank=True)
    finished = models.BooleanField(blank=True)
    size = models.BigIntegerField(null=True, blank=True)
    datecreated = models.DateTimeField(auto_now_add=True)
    dateedited = models.DateTimeField(auto_now=True)
    datatransmission = models.ForeignKey('mediaviewer.DataTransmission',
                                         null=True,
                                         db_column='datatransmissionid',
                                         blank=True)
    _searchString = models.TextField(db_column='searchstr',
                                     blank=True,
                                     null=True)
    imdb_id = models.TextField(db_column='imdb_id',
                               blank=True,
                               null=True)
    hide = models.BooleanField(db_column='hide', default=False)
    filenamescrapeformat = models.ForeignKey('mediaviewer.FilenameScrapeFormat',
                                             null=True,
                                             db_column='filenamescrapeformatid',
                                             blank=True)
    streamable = models.BooleanField(db_column='streamable', null=False, default=True)
    override_filename = models.TextField(blank=True)
    override_season = models.TextField(blank=True)
    override_episode = models.TextField(blank=True)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'file'

    @classmethod
    def new(cls,
            filename,
            path,
            skip=True,
            finished=True,
            size=None,
            datatransmission=None,
            hide=False,
            streamable=True):
        obj = cls()
        obj.filename = filename
        obj.path = path
        obj.skip = skip
        obj.finished = finished
        obj.size = size
        obj.datatransmission = datatransmission
        obj.hide = hide
        obj.streamable = streamable
        obj.save()
        return obj

    @property
    def isFile(self):
        return True

    @property
    def isPath(self):
        return False

    def _get_pathid(self):
        return self.path.id
    def _set_pathid(self, val):
        from mediaviewer.models.path import Path
        path = Path.objects.get(pk=val)
        self.path = path
    pathid = property(fget=_get_pathid, fset=_set_pathid)

    def dateCreatedForSpan(self):
        return self.datecreated and self.datecreated.isoformat()

    @property
    def fileName(self):
        return self.filename

    @property
    def dataTransmission(self):
        return self.datatransmission


    def _posterfileget(self):
        from mediaviewer.models.posterfile import PosterFile
        posterfile = PosterFile.new(file=self)

        return posterfile

    def _posterfileset(self, val):
        val.file = self
        val.save()
    posterfile = property(fset=_posterfileset, fget=_posterfileget)

    def isMovie(self):
        return self.path.is_movie

    def ismovie(self):
        return self.isMovie()

    def isTVShow(self):
        return not self.isMovie()

    def downloadLink(self, user, guid):
        settings = user.settings()
        if not settings or settings.ip_format == LOCAL_IP:
            if self.isMovie():
                waiter_server = '%s%s%s/' % (WAITER_HEAD,
                                             LOCAL_WAITER_IP_FORMAT_MOVIES,
                                             guid)
            else:
                waiter_server = '%s%s%s/' % (WAITER_HEAD,
                                             LOCAL_WAITER_IP_FORMAT_TVSHOWS,
                                             guid)
        elif settings and settings.ip_format == BANGUP_IP:
            if self.isMovie():
                waiter_server = '%s%s%s/' % (WAITER_HEAD,
                                             BANGUP_WAITER_IP_FORMAT_MOVIES,
                                             guid)
            else:
                waiter_server = '%s%s%s/' % (WAITER_HEAD,
                                             BANGUP_WAITER_IP_FORMAT_TVSHOWS,
                                             guid)

        return waiter_server

    def autoplayDownloadLink(self, user, guid):
        if self.isMovie():
            return None
        else:
            return self.downloadLink(user, guid) + 'autoplay'

    def next(self):
        if self.isMovie():
            return None
        else:
            shows = [x for x in self.path.files()]
            shows.sort(key=lambda x: x.displayName())

            index = shows.index(self)
            if index + 1 >= len(shows):
                return None
            else:
                return shows[index + 1]

    def previous(self):
        if self.isMovie():
            return None
        else:
            shows = [x for x in self.path.files()]
            shows.sort(key=lambda x: x.displayName())

            index = shows.index(self)
            if index - 1 < 0:
                return None
            else:
                return shows[index - 1]

    def hasErrors(self):
        return Error.objects.filter(file=self).exclude(ignore=True).exists()

    def errors(self, includeIgnored=False):
        if includeIgnored:
            return self.error_set.all()
        else:
            return Error.objects.filter(file=self).exclude(ignore=True)

    @classmethod
    def tvshows(cls):
        return (cls.objects
                   .filter(path__is_movie=False))

    @classmethod
    def movies(cls):
        return (cls.objects
                   .filter(path__is_movie=True))

    def usercomment(self, user):
        usercomment = (UserComment.objects
                                  .filter(file=self)
                                  .filter(user=user)
                                  .first())
        return usercomment

    def markFileViewed(self, user, viewed):
        usercomment = self.usercomment(user)
        if usercomment:
            usercomment.viewed = viewed
        else:
            usercomment = UserComment()
            usercomment.file = self
            usercomment.user = user
            usercomment.viewed = viewed
            usercomment.datecreated = dateObj.utcnow().replace(tzinfo=utc)

        usercomment.dateedited = dateObj.utcnow().replace(tzinfo=utc)
        usercomment.save()

    def __unicode__(self):
        return 'id: %s f: %s' % (self.id, self.fileName)

    def getSearchTerm(self):
        if self.isMovie():
            searchTerm = yearRegex.sub('', self.filename)
            searchTerm = dvdRegex.sub('', searchTerm)
            searchTerm = formatRegex.sub('', searchTerm)
            searchTerm = punctuationRegex.sub(' ', searchTerm)
            searchTerm = searchTerm.strip()
        else:
            searchTerm = self.path.localPath.rpartition('/')[-1]
            searchTerm = yearRegex.sub('', searchTerm)
            searchTerm = dvdRegex.sub('', searchTerm)
            searchTerm = formatRegex.sub('', searchTerm)
            searchTerm = punctuationRegex.sub(' ', searchTerm)
            searchTerm = searchTerm.strip()

        return searchTerm

    def searchString(self):
        searchStr = self.rawSearchString()
        searchStr = searchStr.replace('&', '%26')
        searchStr = searchStr.replace(',', '%2C')
        searchStr = searchStr.replace('+', '%2B')
        return searchStr

    def rawSearchString(self):
        searchStr = (self.override_filename or
                        self.path.override_display_name or
                        self._searchString or
                        self.getSearchTerm())
        return searchStr

    def getScrapedName(self):
        if self.override_filename:
            return self.override_filename

        if self.path.override_display_name:
            return self.path.override_display_name

        if not self.filenamescrapeformat:
            return self.filename

        if self.filenamescrapeformat.useSearchTerm:
            name = self.rawSearchString()
        else:
            nameRegex = re.compile(
                    self.filenamescrapeformat.nameRegex).findall(self.filename)
            name = nameRegex and nameRegex[0] or None
        return name and (self.filenamescrapeformat.subPeriods and
                         name.replace('.', ' ').replace('-', ' ').title() or
                         name).strip() or self.filename

    def getScrapedSeason(self):
        if not self.override_season:
            if not self.filenamescrapeformat:
                return None

            seasonRegex = re.compile(self.filenamescrapeformat.seasonRegex).findall(self.filename)
            season = seasonRegex and seasonRegex[0] or None
        else:
            season = self.override_season
        return season and (season.isdigit() and season.zfill(2) or None) or None

    def getScrapedEpisode(self):
        if not self.override_episode:
            if not self.filenamescrapeformat:
                return None

            episodeRegex = re.compile(self.filenamescrapeformat.episodeRegex).findall(self.filename)
            episode = episodeRegex and episodeRegex[0] or None
        else:
            episode = self.override_episode
        return episode and (episode.isdigit() and episode.zfill(2) or None) or None

    def getScrapedFullName(self):
        if self.isMovie():
            return self.rawSearchString()
        else:
            name = self.getScrapedName()
            season = self.getScrapedSeason()
            episode = self.getScrapedEpisode()
            if name and season and episode:
                fullname = '%s S%s E%s' % (name, season, episode)
            else:
                fullname = name
            return fullname

    def displayName(self):
        return self.getScrapedFullName()

    def inferScraper(self, scrapers=None):
        if self.isMovie():
            return

        if not scrapers:
            scrapers = FilenameScrapeFormat.objects.all()
        for scraper in scrapers:
            self.filenamescrapeformat = scraper
            name = self.getScrapedName()
            season = self.getScrapedSeason()
            episode = self.getScrapedEpisode()
            sFail = re.compile('\s[sS]$')
            if (name and
                name != self.filename and
                not sFail.findall(name) and
                season and
                episode and
                int(episode) != 64):
                # Success!
                log.debug("Success!!!")
                log.debug('Name: %s Season: %s Episode: %s Fullname: %s FSid: %s' % (name, season, episode, self.filename, scraper.id))
                self.save()
                self.destroyPosterFile()
                break
        else:
            self.filenamescrapeformat = None

    @classmethod
    def inferAllScrapers(cls):
        log.debug('Begin inferring all scrapers')
        files = cls.objects.filter(filenamescrapeformat=None)
        scrapers = FilenameScrapeFormat.objects.all()
        for file in files:
            file.inferScraper(scrapers=scrapers)

    def destroyPosterFile(self):
        try:
            log.debug('Destroying PosterFile for %s' % (self,))
            posterfile = PosterFile.objects.get(file=self)
            posterfile.delete()
        except Exception, e:
            log.error('Got an error destroying posterfile')
            log.error(e)

    @classmethod
    def populate_all_posterfiles(cls):
        all_files = cls.objects.filter(path__is_movie=True).filter(hide=False).all()
        for file in all_files:
            file.posterfile
            time.sleep(.5)

    @classmethod
    def get_movie_genres(cls):
        return Genre.get_movie_genres()
