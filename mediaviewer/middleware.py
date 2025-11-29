from datetime import datetime, timedelta

import secure
from django.conf import settings
from django.contrib import auth

import logging

log = logging.getLogger(__name__)

secure_headers = secure.Secure()


def set_secure_headers(get_response):
    def middleware(request):
        response = get_response(request)
        secure_headers.framework.django(response)
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
                    del request.session["last_touch"]
                    return
        except Exception as e:
            log.error(str(e))

        request.session["last_touch"] = datetime.now().isoformat()
        return self.get_response(request)
