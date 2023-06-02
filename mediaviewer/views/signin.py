import requests

from django.core.exceptions import ValidationError
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.shortcuts import render
from django.contrib.auth import login as login_user
from django.contrib.auth.models import User
from django.contrib.auth.views import INTERNAL_RESET_SESSION_TOKEN
from django.contrib.auth.tokens import default_token_generator
from mediaviewer.models.loginevent import LoginEvent
from django.conf import settings as conf_settings
from mediaviewer.models.usersettings import ImproperLogin
from mediaviewer.models.sitegreeting import SiteGreeting
from mediaviewer.utils import logAccessInfo
from django.contrib.auth.signals import user_logged_in, user_login_failed
from mediaviewer.views.views_utils import setSiteWideContext
from django.http import HttpResponseRedirect, JsonResponse


def get_user(uidb64):
    try:
        # urlsafe_base64_decode() decodes to bytestring
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (
        TypeError,
        ValueError,
        OverflowError,
        User.DoesNotExist,
        ValidationError,
    ):
        user = None
    return user


def create_token_failed(request):
    context = {}
    return render(request, "mediaviewer/passkey_create_failed.html", context)


@csrf_exempt
def create_token(request, uidb64):
    reset_token = request.session.get(INTERNAL_RESET_SESSION_TOKEN)
    ref_user = get_user(uidb64)
    if not default_token_generator.check_token(ref_user, reset_token):
        raise ImproperLogin("Invalid Token")

    payload = {
        "userId": ref_user.username,
        "username": ref_user.username,
        "aliasHashing": False,
    }

    resp = requests.post(
        f"{conf_settings.PASSKEY_API_URL}/register/token",
        json=payload,
        headers={
            "ApiSecret": conf_settings.PASSKEY_API_PRIVATE_KEY,
        },
        timeout=conf_settings.REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return JsonResponse(resp.json())


def create_token_complete(request):
    context = {}
    return render(request, "mediaviewer/passkey_complete.html", context)


@csrf_exempt
def verify_token(request):
    token = request.GET["token"]

    payload = {"token": token}

    resp = requests.post(
        f"{conf_settings.PASSKEY_API_URL}/signin/verify",
        json=payload,
        headers={
            "ApiSecret": conf_settings.PASSKEY_API_PRIVATE_KEY,
        },
        timeout=conf_settings.REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    json_data = resp.json()

    try:
        user = User.objects.get(username__iexact=json_data["userId"])
    except Exception:
        user = User.objects.get(pk=json_data["userId"])

    context = {"loggedin": False}
    siteGreeting = SiteGreeting.latestSiteGreeting()
    context["active_page"] = "signin"
    context["greeting"] = siteGreeting and siteGreeting.greeting or "SignIn"

    if "next" in request.GET:
        context["next"] = request.GET["next"]

    try:
        if not user.settings().can_login:
            user_login_failed.send(
                sender=User,
                credentials={"username": user.username},
                request=request,
            )
            raise ImproperLogin("User could not be logged in. E101")
        else:
            if user.is_active:
                login_user(
                    request, user, backend="django.contrib.auth.backends.ModelBackend"
                )
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
                    credentials={"username": user.username},
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


@logAccessInfo
def signin(request):
    context = {"loggedin": False}
    siteGreeting = SiteGreeting.latestSiteGreeting()
    context["active_page"] = "signin"
    context["greeting"] = siteGreeting and siteGreeting.greeting or "SignIn"

    if "next" in request.GET:
        context["next"] = request.GET["next"]

    return render(request, "mediaviewer/signin.html", context)
