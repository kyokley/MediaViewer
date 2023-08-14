from django.contrib.auth.models import User
from django.shortcuts import render
from mediaviewer.views.views_utils import setSiteWideContext
from django.contrib.auth import logout
from django.contrib.auth.signals import user_logged_out
from mediaviewer.utils import logAccessInfo


@logAccessInfo
def signout(request):
    settings = request.user.settings() if hasattr(request.user, "settings") else None
    logout(request)
    context = {}
    context["active_page"] = "logout"
    context["loggedin"] = False
    context["title"] = "Signed out"
    setSiteWideContext(context, request)
    if settings:
        context["theme"] = settings.theme
    request.session["theme"] = context["theme"]

    user_logged_out.send(
        sender=User,
        request=request,
        user=request.user,
    )
    return render(request, "mediaviewer/logout.html", context)
