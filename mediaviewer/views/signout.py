from django.contrib.auth.models import User
from django.urls import reverse
from django.shortcuts import redirect
from urllib.parse import quote_plus, urlencode
from django.conf import settings as conf_settings
from mediaviewer.utils import logAccessInfo
from mediaviewer.views.views_utils import setSiteWideContext
from django.contrib.auth.signals import user_logged_out
from django.shortcuts import render


def logout(request):
    request.session.clear()

    return redirect(
        f"https://{conf_settings.AUTH0_DOMAIN}/v2/logout?"
        + urlencode(
            {
                "returnTo": request.build_absolute_uri(reverse("mediaviewer:home")),
                "client_id": conf_settings.AUTH0_CLIENT_ID,
            },
            quote_via=quote_plus,
        ),
    )


@logAccessInfo
def signout(request):
    logout(request)
    context = {}
    context["active_page"] = "logout"
    context["loggedin"] = False
    context["title"] = "Signed out"
    setSiteWideContext(context, request)

    user_logged_out.send(
        sender=User,
        request=request,
        user=request.user,
    )
    return render(request, "mediaviewer/logout.html", context)
