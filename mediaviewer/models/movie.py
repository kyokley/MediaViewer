import re

from django.db import models
from .media import Media, MediaManager, MediaQuerySet
from mediaviewer.models import MediaPath, MediaFile
from .poster import Poster
from django.urls import reverse
from .core import ViewableObjectMixin, ViewableManagerMixin

yearRegex = re.compile(r"(19|20)\d{2}\D?.*$")
dvdRegex = re.compile(r"[A-Z]{2,}.*$")
formatRegex = re.compile(r"\b(xvid|avi|XVID|AVI)+\b")
punctuationRegex = re.compile(r"[^a-zA-Z0-9]+")


class MovieQuerySet(MediaQuerySet):
    pass


class MovieManager(MediaManager, ViewableManagerMixin):
    def from_filename(self,
                      filename,
                      path,
                      display_name='',
                      ):
        mp = MediaPath.objects.filter(_path=path).first()
        if mp:
            movie = mp.movie
            if not movie:
                raise ValueError(f'No movie found for the given path {path}')
        else:
            movie, created = super().from_filename(filename)
            Poster.objects.from_ref_obj(movie)

            mp = MediaPath.objects.create(
                _path=path,
                movie=movie)

        mf = MediaFile.objects.create(
            media_path=mp,
            filename=filename,
            display_name=display_name,
        )
        Poster.objects.from_ref_obj(mf)
        return movie, mf

    @staticmethod
    def scrape_filename(filename):
        searchTerm = yearRegex.sub("", filename)
        searchTerm = dvdRegex.sub("", searchTerm)
        searchTerm = formatRegex.sub("", searchTerm)
        searchTerm = punctuationRegex.sub(" ", searchTerm)
        searchTerm = searchTerm.strip()
        return searchTerm


class Movie(Media, ViewableObjectMixin):
    poster = models.OneToOneField('mediaviewer.Poster',
                                  null=True,
                                  on_delete=models.SET_NULL,
                                  blank=True,
                                  related_name='movie')

    objects = MovieManager.from_queryset(MovieQuerySet)()

    def is_tv(self):
        return False

    def url(self):
        return '<a href="{}">{}</a>'.format(
            reverse("mediaviewer:moviedetail", args=(self.id,)), self.full_name
        )

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
            f'<a class="img-preview" href="/mediaviewer/moviedetail/{self.id}/" data-bs-toggle="popover" data-bs-trigger="hover focus" data-container="body" {tooltip_img}>{self.name}</a>',
            f"""<span class="hidden_span">{self.date_created.isoformat()}</span>{self.date_created.date().strftime('%b %d, %Y')}""",
        ]

        if can_download:
            if waiterstatus:
                payload.append(
                    f"""<center><a class='btn btn-info' name='download-btn' id={self.id} target=_blank rel="noopener noreferrer" onclick="openDownloadWindow('{self.id}', 'movie')">Open</a></center>"""
                )
            else:
                payload.append("Alfred is down")

        cell = """<div class="row text-center">"""
        if self.comments.filter(user=user,
                                viewed=True).exists():
            cell = f"""{cell}<input class="viewed-checkbox" name="{ self.id }" type="checkbox" checked onclick="ajaxMovieCheckBox(['{self.id}'])" />"""
        else:
            cell = f"""{cell}<input class="viewed-checkbox" name="{ self.id }" type="checkbox" onclick="ajaxMovieCheckBox(['{self.id}'])" />"""
        cell = f'{cell}<span id="saved-{ self.id }"></span></div>'
        payload.extend(
            [
                cell,
                f"""<input class='report' name='report-{ self.id }' value='Report' type='button' onclick="reportButtonClick('{self.id}', 'movie')"/>""",
            ]
        )
        return payload
