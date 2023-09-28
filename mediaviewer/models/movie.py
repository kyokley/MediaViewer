from django.db import models
from .media import Media, MediaManager, MediaQuerySet


class MovieQuerySet(MediaQuerySet):
    pass


class MovieManager(MediaManager):
    pass


class Movie(Media):
    poster = models.OneToOneField('mediaviewer.Poster',
                                  null=True,
                                  on_delete=models.SET_NULL,
                                  blank=True,
                                  related_name='movie')

    objects = MovieManager.from_queryset(MovieQuerySet)()

    def is_tv(self):
        return False

    def ajax_row_payload(self, can_download, waiterstatus, viewed_lookup):
        poster = self.poster
        tooltip_img = (
            f"""data-bs-content="<img class='tooltip-img' src='{ poster.image.url }' />\""""
            if poster and poster.image
            else ""
        )

        payload = [
            f'<a class="img-preview" href="/mediaviewer/movie/{self.id}/" data-bs-toggle="popover" data-bs-trigger="hover focus" data-container="body" {tooltip_img}>{self._display_name}</a>',
            f"""<span class="hidden_span">{self.date_created.isoformat()}</span>{self.date_created.date().strftime('%b %d, %Y')}""",
        ]

        if can_download:
            if waiterstatus:
                payload.append(
                    f"""<center><a class='btn btn-info' name='download-btn' id={self.id} target=_blank rel="noopener noreferrer" onclick="openDownloadWindow('{self.id}')">Open</a></center>"""
                )
            else:
                payload.append("Alfred is down")

        cell = """<div class="row text-center">"""
        if viewed_lookup.get(self.id, False):
            cell = f"""{cell}<input class="viewed-checkbox" name="{ self.id }" type="checkbox" checked onclick="ajaxCheckBox(['{self.id}'])" />"""
        else:
            cell = f"""{cell}<input class="viewed-checkbox" name="{ self.id }" type="checkbox" onclick="ajaxCheckBox(['{self.id}'])" />"""
        cell = f'{cell}<span id="saved-{ self.id }"></span></div>'
        payload.extend(
            [
                cell,
                f"""<input class='report' name='report-{ self.id }' value='Report' type='button' onclick="reportButtonClick('{self.id}')"/>""",
            ]
        )
        return payload
