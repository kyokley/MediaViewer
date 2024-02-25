import re

from django.db import models
from django.urls import reverse

from mediaviewer.models import MediaPath

from .core import ViewableManagerMixin, ViewableObjectMixin
from .media import Media, MediaManager, MediaQuerySet
from .poster import Poster

yearRegex = re.compile(r"(19|20)\d{2}\D?.*$")
dvdRegex = re.compile(r"[A-Z]{2,}.*$")
formatRegex = re.compile(r"\b(xvid|avi|XVID|AVI)+\b")
punctuationRegex = re.compile(r"[^a-zA-Z0-9]+")


class MovieQuerySet(MediaQuerySet):
    pass


class MovieManager(MediaManager, ViewableManagerMixin):
    def from_path(
        self,
        path,
        name=None,
        tv_id=None,
        movie_id=None,
    ):
        if tv_id is not None:
            raise ValueError('tv_id is not allowed for Movie objects')

        mp = MediaPath.objects.filter(_path=path).first()
        if mp:
            movie = mp.movie
            if not movie:
                raise ValueError(f"No movie found for the given path {path}")
        else:
            if movie_id is None:
                movie, created = super().from_path(path, name=name)
            else:
                movie = self.get(pk=movie_id)
            Poster.objects.from_ref_obj(movie)

            mp = MediaPath.objects.create(_path=path, movie=movie)

        return movie

    @staticmethod
    def scrape_filename(filename):
        searchTerm = yearRegex.sub("", filename)
        searchTerm = dvdRegex.sub("", searchTerm)
        searchTerm = formatRegex.sub("", searchTerm)
        searchTerm = punctuationRegex.sub(" ", searchTerm)
        searchTerm = searchTerm.strip()
        return searchTerm


class Movie(Media, ViewableObjectMixin):
    _poster = models.OneToOneField(
        "mediaviewer.Poster",
        null=True,
        on_delete=models.SET_NULL,
        blank=True,
        related_name="movie",
    )

    objects = MovieManager.from_queryset(MovieQuerySet)()

    def is_tv(self):
        return False

    def url(self):
        return '<a href="{}">{}</a>'.format(
            reverse("mediaviewer:moviedetail", args=(self.id,)), self.full_name
        )

    def next(self):
        return None

    def previous(self):
        return None

    def last_watched_url(self):
        return self.url()

    def ajax_row_payload(self, can_download, waiterstatus, user):
        poster = self.poster
        tooltip_img = (
            f"""data-bs-content="<img class='tooltip-img' src='{ poster.image.url }' />\""""
            if poster and poster.image
            else ""
        )

        payload = [
            f'<a class="img-preview" href="/mediaviewer/moviedetail/{self.id}/" data-bs-toggle="popover" data-bs-trigger="hover focus" data-container="body" data-bs-custom-class="preview-tooltip" {tooltip_img}>{self.name}</a>',
            f"""<center><span class="hidden_span">{self.date_created.isoformat()}</span>{self.date_created.date().strftime('%b %d, %Y')}</center>""",
        ]

        if can_download:
            if waiterstatus:
                payload.append(
                    f"""<center><a class='btn btn-info' name='download-btn' id={self.id} target=_blank rel="noopener noreferrer" onclick="openDownloadWindow('{self.id}', 'movie')">Open</a></center>"""
                )
            else:
                payload.append("Alfred is down")

        cell = """<center>"""
        if self.comments.filter(user=user, viewed=True).exists():
            cell = f"""{cell}<input class="viewed-checkbox" name="{ self.id }" type="checkbox" checked onclick="ajaxMovieCheckBox(['{self.id}'])" />"""
        else:
            cell = f"""{cell}<input class="viewed-checkbox" name="{ self.id }" type="checkbox" onclick="ajaxMovieCheckBox(['{self.id}'])" />"""
        cell = f'{cell}<span id="saved-{ self.id }"></span></center>'
        payload.extend(
            [
                cell,
                f"""<center><input class='report' name='report-{ self.id }' value='Report' type='button' onclick="reportButtonClick('{self.id}', 'movie')"/></center>""",
            ]
        )
        return payload
