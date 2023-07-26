import re
import time

from django.db import models
from django.urls import reverse
from django.utils.timezone import utc

from mediaviewer.models.posterfile import PosterFile
from mediaviewer.models.error import Error
from mediaviewer.models.usercomment import UserComment
from mediaviewer.models.filenamescrapeformat import FilenameScrapeFormat
from mediaviewer.models.genre import Genre
from mediaviewer.models.message import Message
from datetime import datetime as dateObj

from django.conf import settings as conf_settings
from mediaviewer.models.usersettings import LOCAL_IP, BANGUP_IP, UserSettings
from mediaviewer.log import log
from mediaviewer.utils import get_search_query

yearRegex = re.compile(r"20\d{2}\D?.*$")
dvdRegex = re.compile(r"[A-Z]{2,}.*$")
formatRegex = re.compile(r"\b(xvid|avi|XVID|AVI)+\b")
punctuationRegex = re.compile(r"[^a-zA-Z0-9]+")


class FileQuerySet(models.QuerySet):
    def search(self, search_str):
        qs = self
        if search_str:
            filename_query = get_search_query(search_str, ["filename"])

            qs = qs.filter(filename_query)
        return qs


class FileManager(models.Manager):
    def create(self, *args, **kwargs):
        obj = super().create(*args, **kwargs)

        path = kwargs["path"]

        # Generate continue watching messages
        settings = UserSettings.objects.filter(last_watched=path).all()
        for setting in settings:
            Message.createLastWatchedMessage(setting.user, obj)

        return obj


class File(models.Model):
    path = models.ForeignKey(
        "mediaviewer.Path",
        on_delete=models.CASCADE,
        null=True,
        db_column="pathid",
        blank=True,
    )
    filename = models.TextField(blank=True)
    skip = models.BooleanField(blank=True, default=False)
    finished = models.BooleanField(blank=True, default=True)
    size = models.BigIntegerField(null=True, blank=True)
    datecreated = models.DateTimeField(auto_now_add=True)
    dateedited = models.DateTimeField(auto_now=True)
    _searchString = models.TextField(db_column="searchstr", blank=True, null=True)
    imdb_id = models.TextField(db_column="imdb_id", blank=True, null=True)
    hide = models.BooleanField(db_column="hide", default=False)
    filenamescrapeformat = models.ForeignKey(
        "mediaviewer.FilenameScrapeFormat",
        on_delete=models.CASCADE,
        null=True,
        db_column="filenamescrapeformatid",
        blank=True,
    )
    streamable = models.BooleanField(db_column="streamable", null=False, default=True)
    override_filename = models.TextField(blank=True)
    override_season = models.TextField(blank=True)
    override_episode = models.TextField(blank=True)

    users = models.ManyToManyField("auth.User", through="UserComment")

    objects = FileManager.from_queryset(FileQuerySet)()

    class Meta:
        app_label = "mediaviewer"
        db_table = "file"

    @classmethod
    def new(
        cls,
        filename,
        path,
        skip=True,
        finished=True,
        size=None,
        hide=False,
        streamable=True,
    ):
        obj = cls()
        obj.filename = filename
        obj.path = path
        obj.skip = skip
        obj.finished = finished
        obj.size = size
        obj.hide = hide
        obj.streamable = streamable
        obj.save()

        # Generate continue watching messages
        settings = UserSettings.objects.filter(last_watched=path).all()
        for setting in settings:
            Message.createLastWatchedMessage(setting.user, obj)
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

    def _posterfileget(self):
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
                waiter_server = f"{conf_settings.WAITER_HEAD}{conf_settings.LOCAL_WAITER_IP_FORMAT_MOVIES}{guid}/"
            else:
                waiter_server = f"{conf_settings.WAITER_HEAD}{conf_settings.LOCAL_WAITER_IP_FORMAT_TVSHOWS}{guid}/"
        elif settings and settings.ip_format == BANGUP_IP:
            if self.isMovie():
                waiter_server = f"{conf_settings.WAITER_HEAD}{conf_settings.BANGUP_WAITER_IP_FORMAT_MOVIES}{guid}/"
            else:
                waiter_server = f"{conf_settings.WAITER_HEAD}{conf_settings.BANGUP_WAITER_IP_FORMAT_TVSHOWS}{guid}/"

        return waiter_server

    def autoplayDownloadLink(self, user, guid):
        if self.isMovie():
            return None
        else:
            return self.downloadLink(user, guid) + "autoplay"

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
        return cls.objects.filter(path__is_movie=False)

    @classmethod
    def movies(cls):
        return cls.objects.filter(path__is_movie=True)

    def usercomment(self, user):
        usercomment = UserComment.objects.filter(file=self).filter(user=user).first()
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

        if not self.next():
            Message.clearLastWatchedMessage(user)

    def __str__(self):
        return f"id: {self.id} f: {self.fileName}"

    def url(self):
        return '<a href="{}">{}</a>'.format(
            reverse("mediaviewer:filesdetail", args=(self.id,)), self.displayName()
        )

    def getSearchTerm(self):
        if self.isMovie():
            searchTerm = yearRegex.sub("", self.filename)
            searchTerm = dvdRegex.sub("", searchTerm)
            searchTerm = formatRegex.sub("", searchTerm)
            searchTerm = punctuationRegex.sub(" ", searchTerm)
            searchTerm = searchTerm.strip()
        else:
            searchTerm = self.path.localPath.rpartition("/")[-1]
            searchTerm = yearRegex.sub("", searchTerm)
            searchTerm = dvdRegex.sub("", searchTerm)
            searchTerm = formatRegex.sub("", searchTerm)
            searchTerm = punctuationRegex.sub(" ", searchTerm)
            searchTerm = searchTerm.strip()

        return searchTerm

    def searchString(self):
        searchStr = self.rawSearchString()
        searchStr = searchStr.replace("&", "%26")
        searchStr = searchStr.replace(",", "%2C")
        searchStr = searchStr.replace("+", "%2B")
        return searchStr

    def rawSearchString(self):
        searchStr = (
            self.override_filename
            or self.path.override_display_name
            or self._searchString
            or self.getSearchTerm()
        )
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
            nameRegex = re.compile(self.filenamescrapeformat.nameRegex).findall(
                self.filename
            )
            name = nameRegex and nameRegex[0] or None
        return (
            name
            and (
                self.filenamescrapeformat.subPeriods
                and name.replace(".", " ").replace("-", " ").title()
                or name
            ).strip()
            or self.filename
        )

    def getScrapedSeason(self):
        if not self.override_season:
            if not self.filenamescrapeformat:
                return None

            seasonRegex = re.compile(self.filenamescrapeformat.seasonRegex).findall(
                self.filename
            )
            season = seasonRegex and seasonRegex[0] or None
        else:
            season = self.override_season
        return season and (season.isdigit() and season.zfill(2) or None) or None

    def getScrapedEpisode(self):
        if not self.override_episode:
            if not self.filenamescrapeformat:
                return None

            episodeRegex = re.compile(self.filenamescrapeformat.episodeRegex).findall(
                self.filename
            )
            episode = episodeRegex and episodeRegex[0] or None
        else:
            episode = self.override_episode
        return episode and (episode.isdigit() and episode.zfill(2) or None) or None

    def getScrapedFullName(self, include_path_name=True):
        if self.isMovie():
            return self.rawSearchString()
        else:
            name = (
                self.posterfile.episodename
                if self.posterfile and self.posterfile.episodename
                else self.getScrapedName()
            )
            season = self.getScrapedSeason()
            episode = self.getScrapedEpisode()
            if name and season and episode:
                if include_path_name:
                    fullname = f"{self.path.displayName()} S{season} E{episode}: {name}"
                else:
                    fullname = f"S{season} E{episode}: {name}"
            else:
                fullname = name
            return fullname

    def displayName(self):
        return self.getScrapedFullName(include_path_name=False)

    def display_name_with_path(self):
        return self.getScrapedFullName(include_path_name=True)

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
            sFail = re.compile(r"\s[sS]$")
            if (
                name
                and name != self.filename
                and not sFail.findall(name)
                and season
                and episode
                and int(episode) != 64
            ):
                # Success!
                log.debug("Success!!!")
                log.debug(
                    f"Name: {name} Season: {season} Episode: {episode} Fullname: {self.filename} FSid: {scraper.id}"
                )
                self.save()
                self.destroyPosterFile()
                break
        else:
            self.filenamescrapeformat = None

    @classmethod
    def inferAllScrapers(cls):
        log.debug("Begin inferring all scrapers")
        files = cls.objects.filter(filenamescrapeformat=None)
        scrapers = FilenameScrapeFormat.objects.all()
        for file in files:
            file.inferScraper(scrapers=scrapers)

    def destroyPosterFile(self):
        try:
            log.debug(f"Destroying PosterFile for {self}")
            posterfile = PosterFile.objects.get(file=self)
            posterfile.delete()
        except PosterFile.DoesNotExist:
            log.debug("Posterfile does not exist. Continuing.")
        except Exception as e:
            log.error("Got an error destroying posterfile")
            log.error(e)

    @classmethod
    def populate_all_posterfiles(cls, batch=None):
        all_files = cls.objects.exclude(
            pk__in=PosterFile.objects.filter(file__isnull=False).values("file")
        ).order_by("-id")

        if batch:
            all_files = all_files[:batch]

        missing_count = all_files.count()
        fixed_count = 0
        for file in all_files:
            file.posterfile
            fixed_count += 1
            time.sleep(0.25)

            if fixed_count % 10 == 0:
                print(f"Fixed {fixed_count} of {missing_count}")
        print(f"Fixed {fixed_count} of {missing_count}")

    @classmethod
    def get_movie_genres(cls):
        return Genre.get_movie_genres()

    @classmethod
    def movies_ordered_by_id(cls):
        files = cls.movies().filter(hide=False).order_by("-id")
        return files

    # TODO: Test the following functions
    @classmethod
    def movies_by_genre(cls, genre):
        files = (
            cls.objects.filter(_posterfile__genres=genre)
            .filter(hide=False)
            .filter(path__is_movie=True)
        )
        return files

    @classmethod
    def files_by_localpath(cls, localpath):
        files = cls.objects.filter(path__localpathstr=localpath.localpathstr).filter(
            hide=False
        )
        return files

    @classmethod
    def most_recent_files(cls, items=10):
        files = (
            cls.objects.filter(hide=False).filter(finished=True).order_by("-id")[:items]
        )
        return files

    def display_payload(self):
        payload = {
            "id": self.id,
            "name": self.displayName(),
            "dateCreatedForSpan": self.dateCreatedForSpan(),
            "date": self.datecreated.date(),
        }
        return payload

    def ajax_row_payload(self, can_download, waiterstatus, viewed_lookup):
        payload = [
            f'<a href="/mediaviewer/files/{self.id}/">{self.displayName()}</a>',
            f"""<span class="hidden_span">{self.dateCreatedForSpan()}</span>{self.datecreated.date().strftime('%b %d, %Y')}""",
        ]

        if can_download:
            if waiterstatus:
                payload.append(
                    f"""<center><a class='btn btn-info' name='download-btn' id={self.id} target=_blank rel="noopener noreferrer" onclick="openDownloadWindow('{self.id}')">Open</a></center>"""
                )
            else:
                payload.append("Alfred is down")

        if viewed_lookup.get(self.id, False):
            cell = f"""<span class="hidden" name="hidden-{ self.id }">true</span><input name="{ self.id }" type="checkbox" checked onclick="ajaxCheckBox('{self.id}')" />"""
        else:
            cell = f"""<span class="hidden" name="hidden-{ self.id }">false</span><input name="{ self.id }" type="checkbox" onclick="ajaxCheckBox('{self.id}')" />"""
        cell = f'{cell}<span id="saved-{ self.id }"></span>'
        payload.extend(
            [
                cell,
                f"""<input class='report' name='report-{ self.id }' value='Report' type='button' onclick="reportButtonClick('{self.id}')"/>""",
                "",
            ]
        )
        return payload
