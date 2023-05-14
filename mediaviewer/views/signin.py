import base64
import json
from django.urls import reverse
from django.shortcuts import redirect, render
from django.contrib.auth import login as login_user, authenticate
from django.contrib.auth.models import User
from mediaviewer.models.loginevent import LoginEvent
from django.http import JsonResponse
from django.conf import settings as conf_settings
from mediaviewer.models.usersettings import ImproperLogin, case_insensitive_authenticate
from authlib.integrations.django_client import OAuth
from mediaviewer.models.usersettings import UserSettings
from django.views.decorators.csrf import csrf_exempt
from mediaviewer.forms import notify_admin_of_new_user
from mediaviewer.models.sitegreeting import SiteGreeting
from mediaviewer.utils import logAccessInfo
from django.contrib.auth.signals import user_logged_in, user_login_failed
from mediaviewer.views.views_utils import setSiteWideContext
from django.http import HttpResponseRedirect


if conf_settings.USE_AUTH0:
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


def _decode_auth_header(headers):
    basic_auth = base64.b64decode(
        headers['Authorization'].split()[-1]).decode('utf-8')

    username = basic_auth.split(':')[0]
    password = basic_auth.split(':')[1]
    return username, password


def _user_info_from_body(body):
    data = json.loads(body) if body else {
        'email': None,
        'username': None,
        'password': None,
    }
    return data


def _user_info_from_request(request, email=None):
    data = json.loads(request.body) if request.body else {'email': email}

    try:
        username, password = _decode_auth_header(request.headers)
    except Exception:
        username = None
        password = None

    data['username'] = username
    data['password'] = password

    if data['email'] is None:
        data['email'] = username
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


def _validate_auth_auth0(request):
    username, password = _decode_auth_header(request.headers)
    user = None
    if username == conf_settings.AUTH0_LOGIN:
        user = authenticate(username=username,
                            password=password)
    return user


def legacy_verify(request):
    request_user = _validate_auth_auth0(request)
    if request_user is None:
        return JsonResponse({}, status=401)

    data = _user_info_from_request(request)
    user = case_insensitive_authenticate(
        request=request, username=data['username'], password=data['password']
    )

    if user is None:
        return JsonResponse({}, status=404)
    else:
        return JsonResponse({'user_id': user.pk,
                             'nickname': user.username,
                             'email': user.email})


@csrf_exempt
def legacy_user(request, email=None, pk=None):
    if request.method in ('POST', 'PUT', 'DELETE') or email is not None:
        request_user = _validate_auth_auth0(request)
        if request_user is None:
            return JsonResponse({}, status=401)

        data = _user_info_from_body(request.body)
    else:
        username, password = _decode_auth_header(request.headers)
        data = {}
        data['username'] = username
        data['password'] = password

    user = None
    if request.method in ('GET', 'PUT'):
        try:
            if email:
                email = email.strip()
                user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return JsonResponse({}, status=404)

        if user is None:
            try:
                user = User.objects.get(username__iexact=data['username'])
            except User.DoesNotExist:
                return JsonResponse({}, status=401)

        if request.method == 'PUT':
            user.set_password(data['password'])
            user.save()
    elif request.method == 'POST':
        data = _user_info_from_body(request.body)
        user = UserSettings.new(
            data.get('username', data['email']),
            data['email'],
            can_download=False,
            send_email=False,
            verified=False,
        )
        user.set_password(data['password'])
        user.save()

        notify_admin_of_new_user(data['email'])
    elif request.method == 'DELETE':
        if pk is not None:
            User.objects.filter(pk=pk).delete()
            return JsonResponse({}, status=200)

    if user:
        return JsonResponse({'user_id': user.pk,
                            'nickname': user.username,
                            'email': user.email})
    return JsonResponse({}, status=400)


@csrf_exempt
def verify_email(request):
    if request.method == 'PUT':
        request_user = _validate_auth_auth0(request)
        if request_user is None:
            return JsonResponse({}, status=401)

        data = _user_info_from_body(request.body)
        UserSettings.objects.filter(user__email__iexact=data['email']).update(verified=True)
        return JsonResponse({})


@logAccessInfo
def signin(request):
    context = {"loggedin": False}
    siteGreeting = SiteGreeting.latestSiteGreeting()
    context["active_page"] = "signin"
    context["greeting"] = siteGreeting and siteGreeting.greeting or "SignIn"
    user = request.user

    if "next" in request.GET:
        context["next"] = request.GET["next"]

    if not user.is_authenticated:
        try:
            if request.method == "POST":
                username = request.POST["username"]
                password = request.POST["password"]
                user = case_insensitive_authenticate(
                    request=request, username=username, password=password
                )
                if user is None:
                    user_login_failed.send(
                        sender=User,
                        credentials={"username": username, "password": password},
                        request=request,
                    )
                    raise Exception("Incorrect username or password!")
                elif not user.settings().can_login:
                    user_login_failed.send(
                        sender=User,
                        credentials={"username": username, "password": password},
                        request=request,
                    )
                    raise ImproperLogin(
                        "You should have received an email with a link "
                        "to set up your password the first time. "
                        "Please follow the instructions in the email."
                    )
                else:
                    if user.is_active:
                        login_user(request, user)
                        context["loggedin"] = True
                        context["user"] = request.user
                        LoginEvent.new(request.user)
                        # TODO: Finish implementing signals
                        user_logged_in.send(
                            sender=User,
                            request=request,
                            user=user,
                        )
                    else:
                        user_login_failed.send(
                            sender=User,
                            credentials={"username": username, "password": password},
                            request=request,
                        )
                        raise ImproperLogin("User is no longer active")

        except ImproperLogin as e:
            context["error_message"] = str(e)
        except Exception as e:
            if conf_settings.DEBUG:
                context["error_message"] = str(e)
            else:
                context["error_message"] = "Incorrect username or password!"

    if user and user.is_authenticated and not context.get("error_message"):
        settings = user.settings()
        setSiteWideContext(context, request)
        if not user.email or settings.force_password_change:
            return HttpResponseRedirect(reverse("mediaviewer:settings"))
        elif "next" in request.POST and request.POST["next"]:
            return HttpResponseRedirect(request.POST["next"])
        else:
            if request.method == "GET":
                return render(request, "mediaviewer/signin.html", context)
            else:
                return HttpResponseRedirect(reverse("mediaviewer:signin"))

    return render(request, "mediaviewer/signin.html", context)
