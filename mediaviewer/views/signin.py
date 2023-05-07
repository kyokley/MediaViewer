import base64
import json
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.auth import login as login_user
from django.contrib.auth.models import User
from mediaviewer.models.loginevent import LoginEvent
from django.http import JsonResponse
from django.conf import settings as conf_settings
from mediaviewer.models.usersettings import case_insensitive_authenticate
from authlib.integrations.django_client import OAuth
from mediaviewer.models.usersettings import UserSettings
from django.views.decorators.csrf import csrf_exempt


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


def _user_info_from_request(request, email=None):
    data = json.loads(request.body) if request.body else {'email': email}

    try:
        basic_auth = base64.b64decode(
            request.headers['Authorization'].split()[-1]).decode('utf-8')

        username = basic_auth.split(':')[0]
        password = basic_auth.split(':')[1]
    except Exception:
        username = None
        password = None

    data['username'] = username
    data['password'] = password
    return data


def callback(request):
    token = oauth.auth0.authorize_access_token(request)
    request.session["user"] = token

    username = token['userinfo'].get('nickname')
    email = token['userinfo'].get('email')

    try:
        user = User.objects.filter(is_active=True).get(username=username)
    except User.DoesNotExist:
        user = User.objects.filter(is_active=True).get(email=email)

    login_user(request, user, backend='django.contrib.auth.backends.ModelBackend')
    LoginEvent.new(request.user)
    return redirect(request.build_absolute_uri(reverse("mediaviewer:home")))


def legacy_verify(request):
    data = _user_info_from_request(request)
    user = case_insensitive_authenticate(
        request=request, username=data['username'], password=data['password']
    )

    if user is None:
        return JsonResponse({}, status=401)
    else:
        return JsonResponse({'user_id': user.pk,
                             'nickname': user.username,
                             'email': user.email})


@csrf_exempt
def legacy_user(request, email=None):
    data = _user_info_from_request(request, email=email)

    if request.method in ('GET', 'PUT'):
        try:
            if data.get('email'):
                user = User.objects.get(email__iexact=data['email'])
            else:
                user = User.objects.get(username__iexact=data['username'])
        except User.DoesNotExist:
            return JsonResponse({}, status=401)

        if request.method == 'PUT':
            user.set_password(data['password'])
            user.save()
    elif request.method == 'POST':
        user = UserSettings.new(
            data['username'],
            data['email'],
            can_download=False,
        )
        user.set_password(data['password'])
        user.save()

    return JsonResponse({'user_id': user.pk,
                         'nickname': user.username,
                         'email': user.email})
