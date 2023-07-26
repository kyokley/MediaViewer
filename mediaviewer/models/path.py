import time
from django.db import models
from django.urls import reverse
from mediaviewer.models.file import File
from mediaviewer.models.posterfile import PosterFile
from mediaviewer.models.usercomment import UserComment
from mediaviewer.models.genre import Genre
from datetime import datetime as dateObj
from datetime import timedelta
from django.utils.timezone import utc

from mediaviewer.utils import get_search_query


class PathQuerySet(models.QuerySet):
    def search(self, search_str):
        qs = self
        if search_str:
            filename_query = get_search_query(
                search_str,
                [
                    "override_display_name",
                    "defaultsearchstr",
                    "localpathstr",
                ],
            )

            qs = qs.filter(filename_query)
        return qs


class Path(models.Model):
    localpathstr = models.TextField(blank=True)
    remotepathstr = models.TextField(blank=True)
    skip = models.BooleanField(blank=True, null=False, default=False)
    is_movie = models.BooleanField(blank=False, null=False, db_column="ismovie")
    defaultScraper = models.ForeignKey(
        "mediaviewer.FilenameScrapeFormat",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_column="defaultscraperid",
    )
    tvdb_id = models.TextField(null=True, blank=True)
    server = models.TextField(blank=False, null=False, default="127.0.0.1")
    defaultsearchstr = models.TextField(null=True, blank=True)
    imdb_id = models.TextField(null=True, blank=True)
    override_display_name = models.TextField(
        null=True, blank=True, db_column="display_name"
    )
    lastCreatedFileDate = models.DateTimeField(
        null=True, blank=True, db_column="lastcreatedfiledate"
    )
    finished = models.BooleanField(
        blank=False,
        null=False,
        default=False,
    )

    objects = models.Manager.from_queryset(PathQuerySet)()

    class Meta:
        app_label = "mediaviewer"
        db_table = "path"

    @property
    def isFile(self):
        return False

    @property
    def isPath(self):
        return True

    def files(self):
        files = set()
        paths = Path.objects.filter(localpathstr=self.localpathstr)
        for path in paths:
            files.update(path.file_set.filter(hide=False))
        return list(files)

    @property
    def shortName(self):
        return self.localPath.rpartition("/")[-1]

    @property
    def localPath(self):
        return self.localpathstr

    localpath = localPath

    @property
    def remotePath(self):
        return self.remotepathstr

    remotepath = remotePath

    def displayName(self):
        return self.override_display_name or self.shortName.replace(".", " ").title()

    def __str__(self):
        return "id: %s r: %s l: %s f: %s" % (
            self.id,
            self.remotePath,
            self.localPath,
            self.finished,
        )

    def lastCreatedFileDateForSpan(self):
        last_date = self.lastCreatedFileDate
        return last_date and last_date.date().isoformat()

    def url(self):
        if self.is_movie:
            raise TypeError("url method does not apply to movie paths")
        return '<a href="{}">{}</a>'.format(
            reverse("mediaviewer:tvshows", args=(self.id,)), self.displayName()
        )

    @classmethod
    def distinctShowFolders(cls):
        paths_qs = (
            Path.objects.filter(is_movie=False)
            .filter(file__hide=False)
            .annotate(num_files=models.Count("file"))
            .filter(num_files__gt=0)
        )

        subquery = models.Subquery(
            Path.objects.filter(localpathstr=models.OuterRef("localpathstr"))
            .order_by("-lastCreatedFileDate")
            .values("pk")[:1]
        )
        paths_qs = Path.objects.filter(
            pk__in=(
                paths_qs.values("localpathstr")
                .annotate(path_pk=subquery)
                .values("path_pk")
            )
        )
        return paths_qs

    def isMovie(self):
        return self.is_movie

    def isTVShow(self):
        return not self.isMovie()

    def _posterfileget(self):
        posterfile = PosterFile.new(path=self)

        return posterfile

    def _posterfileset(self, val):
        val.path = self
        val.save()

    posterfile = property(fset=_posterfileset, fget=_posterfileget)

    def destroy(self):
        self.file_set.all().delete()
        self.delete()

    def unwatched_tv_shows_since_date(self, user, daysBack=30):
        if self.isMovie():
            raise Exception("This function does not apply to movies")

        if daysBack > 0:
            refDate = dateObj.utcnow().replace(tzinfo=utc) - timedelta(days=daysBack)
            files = (
                File.objects.filter(path__localpathstr=self.localpathstr)
                .filter(datecreated__gt=refDate)
                .filter(hide=False)
                .all()
            )
        else:
            files = (
                File.objects.filter(path__localpathstr=self.localpathstr)
                .filter(hide=False)
                .all()
            )
        unwatched_files = set()
        for file in files:
            comment = file.usercomment(user)
            if not comment or not comment.viewed:
                unwatched_files.add(file)

        return unwatched_files

    def number_of_unwatched_shows_since_date(self, user, daysBack=30):
        return len(self.unwatched_tv_shows_since_date(user, daysBack=daysBack))

    def number_of_unwatched_shows(self, user):
        if not user:
            return 0

        files = File.objects.filter(path__localpathstr=self.localpathstr).filter(
            hide=False
        )
        file_count = files.count()
        usercomments_count = (
            UserComment.objects.filter(user=user)
            .filter(file__in=files)
            .filter(viewed=True)
            .count()
        )
        return file_count - usercomments_count

    @classmethod
    def populate_all_posterfiles(cls, batch=None):
        all_paths = (
            cls.objects.filter(is_movie=False)
            .exclude(
                pk__in=PosterFile.objects.filter(path__isnull=False).values("path")
            )
            .order_by("-id")
        )

        if batch:
            all_paths = all_paths[:batch]

        missing_count = all_paths.count()
        fixed_count = 0
        for path in all_paths:
            path.posterfile
            fixed_count += 1
            time.sleep(0.25)

            if fixed_count % 10 == 0:
                print(f"Fixed {fixed_count} of {missing_count}")
        print(f"Fixed {fixed_count} of {missing_count}")

    @classmethod
    def get_tv_genres(cls):
        return Genre.get_tv_genres()

    def ajax_row_payload(self, user):
        unwatched_count = self.number_of_unwatched_shows(user)
        payload = [
            (
                f"""<a href='/mediaviewer/tvshows/{ self.id }/'>{ self.displayName() }</a>\n"""
                f'<span id="unwatched-show-badge-{ self.id }" class="badge alert-info">{unwatched_count or ""}</span>'
            ),
            f"""<span class="hidden_span">{self.lastCreatedFileDateForSpan()}</span>{ self.lastCreatedFileDate.date().strftime('%b %d, %Y')}""",
            "",
        ]
        return payload
