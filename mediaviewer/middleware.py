from datetime import datetime, timedelta
from django.conf import settings
from django.contrib import auth


class AutoLogout:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:

            try:
                if datetime.now() - datetime.fromisoformat(request.session["last_touch"]) > timedelta(
                    0, settings.AUTO_LOGOUT_DELAY * 60, 0
                ):
                    auth.logout(request)
                    del request.session["last_touch"]
                    return
            except KeyError:
                pass

        request.session["last_touch"] = datetime.now().isoformat()
        return self.get_response(request)
