import re
from datetime import datetime, timedelta
from urllib.parse import urlsplit

import secure
from django.conf import settings
from django.contrib import auth
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.cache import patch_vary_headers
from django_htmx.http import HttpResponseClientRedirect
from mediaviewer.log import log

secure_headers = secure.Secure()

_HTMX_VARY_HEADERS = ("HX-Request", "HX-History-Restore-Request")
_NON_APP_PATHS = (
    "/mediaviewer/api/",
    "/mediaviewer/ajax",
    "/mediaviewer/download/",
    "/mediaviewer/player/",
    "/mediaviewer/autoplaydownloadlink/",
)


def _is_app_html_path(path):
    if not path.startswith("/mediaviewer/") or path.startswith(_NON_APP_PATHS):
        return False
    return not re.fullmatch(
        r"/mediaviewer/b2player/[0-9A-Za-z]+/(?:media|captions)/",
        path,
    )


def app_html_responses(get_response):
    def middleware(request):
        response = get_response(request)
        if not _is_app_html_path(request.path):
            return response

        location = response.get("Location")
        destination = urlsplit(location) if location else None
        auth_redirect = getattr(response, "_mediaviewer_auth_redirect", False) or (
            destination and destination.path == "/mediaviewer/login/"
        )
        if (
            request.headers.get("HX-Request") == "true"
            and location
            and auth_redirect
            and 300 <= response.status_code < 400
        ):
            if (
                destination
                and not destination.netloc
                and destination.path.startswith("/mediaviewer/")
                and not destination.path.startswith(_NON_APP_PATHS)
            ):
                client_redirect = HttpResponseClientRedirect(location)
                for header, value in response.items():
                    if header.lower() not in ("location", "content-length"):
                        client_redirect[header] = value
                client_redirect.cookies.update(response.cookies)
                response = client_redirect

        if response.get("Content-Type", "").startswith("text/html"):
            patch_vary_headers(response, _HTMX_VARY_HEADERS)
        return response

    return middleware


def set_secure_headers(get_response):
    def middleware(request):
        response = get_response(request)
        cache_control = response.get("Cache-Control")
        referrer_policy = response.get("Referrer-Policy")
        secure_headers.framework.django(response)
        if cache_control is not None:
            response["Cache-Control"] = cache_control
        if referrer_policy is not None:
            response["Referrer-Policy"] = referrer_policy
        return response

    return middleware


class AutoLogout:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            if request.user.is_authenticated:
                if datetime.now() - datetime.fromisoformat(
                    request.session["last_touch"]
                ) > timedelta(minutes=settings.AUTO_LOGOUT_DELAY):
                    auth.logout(request)
                    response = HttpResponseRedirect(reverse("mediaviewer:home"))
                    response._mediaviewer_auth_redirect = True
                    return response
        except Exception as e:
            log.error(str(e))

        request.session["last_touch"] = datetime.now().isoformat()
        return self.get_response(request)
