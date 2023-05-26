import secure
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib import auth


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
        if request.user.is_authenticated:

            try:
                if datetime.now() - datetime.fromisoformat(
                    request.session["last_touch"]
                ) > timedelta(minutes=settings.AUTO_LOGOUT_DELAY):
                    auth.logout(request)
                    del request.session["last_touch"]
                    return
            except KeyError:
                pass

        request.session["last_touch"] = datetime.now().isoformat()
        return self.get_response(request)
