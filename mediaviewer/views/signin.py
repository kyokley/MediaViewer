import requests
from django.conf import settings as conf_settings
from django.contrib.auth import login as login_user
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import INTERNAL_RESET_SESSION_TOKEN
from django.contrib.auth.views import (
    PasswordResetConfirmView as DjangoPasswordResetConfirmView,
)
from django.contrib.auth.views import (
    PasswordResetDoneView as DjangoPasswordResetDoneView,
)
from django.contrib.auth.views import PasswordResetView as DjangoPasswordResetView
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import csrf_exempt

from mediaviewer.models.loginevent import LoginEvent
from mediaviewer.models.sitegreeting import SiteGreeting
from mediaviewer.models.usersettings import ImproperLogin, case_insensitive_authenticate
from mediaviewer.utils import logAccessInfo
from mediaviewer.views.views_utils import setSiteWideContext


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
    setSiteWideContext(context, request)
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
    setSiteWideContext(context, request)
    return render(request, "mediaviewer/passkey_complete.html", context)


@csrf_exempt
def bypass_passkey(request, uidb64):
    reset_token = request.session.get(INTERNAL_RESET_SESSION_TOKEN)
    ref_user = get_user(uidb64)
    if not default_token_generator.check_token(ref_user, reset_token):
        raise ImproperLogin("Invalid Token")

    user = User.objects.get(pk=ref_user.id)

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
        elif user.is_active:
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
            raise ImproperLogin("User is no longer active. E102")

    except ImproperLogin as e:
        context["error_message"] = str(e)
    except Exception as e:
        if conf_settings.DEBUG:
            context["error_message"] = str(e)
        else:
            context["error_message"] = "Something went wrong! E103"

    setSiteWideContext(context, request)

    if user and user.is_authenticated and not context.get("error_message"):
        request.session["theme"] = context["theme"]
        if "next" in request.GET and request.GET["next"]:
            return HttpResponseRedirect(request.GET["next"])
        else:
            if request.method == "GET":
                return render(request, "mediaviewer/home.html", context)
            else:
                return HttpResponseRedirect(reverse("mediaviewer:signin"))

    return render(request, "mediaviewer/home.html", context)


@csrf_exempt
def verify_token(request):
    token = request.GET["token"]
    next = request.GET.get("next") or request.POST.get("next")

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

    if next:
        payload["next"] = next

    try:
        user = User.objects.get(username__iexact=json_data["userId"])
    except Exception:
        user = User.objects.get(pk=json_data["userId"])

    context = {"loggedin": False}
    siteGreeting = SiteGreeting.latestSiteGreeting()
    context["active_page"] = "signin"
    context["greeting"] = siteGreeting and siteGreeting.greeting or "SignIn"

    if next:
        context["next"] = next

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

    setSiteWideContext(context, request)
    if user and user.is_authenticated and not context.get("error_message"):
        request.session["theme"] = context["theme"]
        settings = user.settings()
        if not user.email or settings.force_password_change:
            return HttpResponseRedirect(reverse("mediaviewer:settings"))
        elif next:
            return HttpResponseRedirect(next)
        else:
            if request.method == "GET":
                return render(request, "mediaviewer/home.html", context)
            else:
                return HttpResponseRedirect(reverse("mediaviewer:signin"))

    return render(request, "mediaviewer/home.html", context)


@logAccessInfo
def signin(request):
    context = {"loggedin": False}
    siteGreeting = SiteGreeting.latestSiteGreeting()
    context["active_page"] = "signin"
    context["greeting"] = siteGreeting and siteGreeting.greeting or "SignIn"

    setSiteWideContext(context, request)

    if "next" in request.GET:
        context["next"] = request.GET["next"]

    return render(request, "mediaviewer/home.html", context)


@csrf_exempt
@logAccessInfo
def legacy_signin(request):
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
                        login_user(
                            request,
                            user,
                            backend="django.contrib.auth.backends.ModelBackend",
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

    setSiteWideContext(context, request)
    if user and user.is_authenticated and not context.get("error_message"):
        request.session["theme"] = context["theme"]
        settings = user.settings()
        if not user.email or settings.force_password_change:
            return HttpResponseRedirect(reverse("mediaviewer:settings"))
        elif "next" in request.POST and request.POST["next"]:
            return HttpResponseRedirect(request.POST["next"])
        else:
            if request.method == "GET":
                return render(request, "mediaviewer/home.html", context)
            else:
                return HttpResponseRedirect(reverse("mediaviewer:home"))

    return render(request, "mediaviewer/home.html", context)


class ContextMixin:
    def get(self, *args, **kwargs):
        resp = super().get(*args, **kwargs)
        setSiteWideContext(resp.context_data, args[0])
        return resp


class PasswordResetView(ContextMixin, DjangoPasswordResetView):
    pass


class PasswordResetConfirmView(ContextMixin, DjangoPasswordResetConfirmView):
    pass


class PasswordResetDoneView(ContextMixin, DjangoPasswordResetDoneView):
    pass
