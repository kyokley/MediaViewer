import base64
from django.urls import reverse
from mediaviewer.models.sitegreeting import SiteGreeting
from django.shortcuts import render, redirect
from mediaviewer.views.views_utils import setSiteWideContext
from django.contrib.auth import login as login_user
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_login_failed
from mediaviewer.models.loginevent import LoginEvent
from django.http import HttpResponseRedirect, JsonResponse
from django.conf import settings as conf_settings
from mediaviewer.utils import logAccessInfo
from mediaviewer.models.usersettings import (
    ImproperLogin,
    case_insensitive_authenticate,
)
from authlib.integrations.django_client import OAuth


oauth = OAuth()

oauth.register(
    "auth0",
    client_id=conf_settings.AUTH0_CLIENT_ID,
    client_secret=conf_settings.AUTH0_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{conf_settings.AUTH0_DOMAIN}/.well-known/openid-configuration",
)


def login(request):
    return oauth.auth0.authorize_redirect(
        request, request.build_absolute_uri(reverse("mediaviewer:callback"))
    )


def callback(request):
    token = oauth.auth0.authorize_access_token(request)
    request.session["user"] = token

    username = token['userinfo']['nickname']
    user = User.objects.filter(is_active=True).get(username=username)
    login_user(request, user, backend='django.contrib.auth.backends.ModelBackend')
    LoginEvent.new(request.user)
    return redirect(request.build_absolute_uri(reverse("mediaviewer:home")))


def verify(request):
    data = base64.b64decode(request.headers['Authorization'].split()[-1]).decode('utf-8')

    username = data.split(':')[0]
    password = data.split(':')[1]
    user = case_insensitive_authenticate(
        request=request, username=username, password=password
    )

    if user is None:
        return JsonResponse({}, status=401)
    else:
        return JsonResponse({'user_id': user.pk,
                             'nickname': user.username,
                             'email': user.email})
