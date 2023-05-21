import requests
import json

from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.shortcuts import render
from django.contrib.auth import login as login_user
from django.contrib.auth.models import User
from mediaviewer.models.loginevent import LoginEvent
from django.conf import settings as conf_settings
from mediaviewer.models.usersettings import ImproperLogin, case_insensitive_authenticate, UserSettings
from mediaviewer.models.sitegreeting import SiteGreeting
from mediaviewer.utils import logAccessInfo
from django.contrib.auth.signals import user_logged_in, user_login_failed
from mediaviewer.views.views_utils import setSiteWideContext
from django.http import HttpResponseRedirect, JsonResponse


@csrf_exempt
def create_token(request):
    json_data = json.loads(request.body)
    username = json_data["username"]
    try:
        ref_user = User.objects.get(username__iexact=username)

    except User.DoesNotExist:
        try:
            ref_user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:

            ref_user = UserSettings.new(username,
                                        username,
                                        verified=True,
                                        can_download=False,
                                        send_email=False,
                                        )

    payload = {'userId': f'{ref_user.pk}',
               'username': username,
               'aliases': [ref_user.username, ref_user.email],
               }

    resp = requests.post(
        f'{conf_settings.PASSKEY_API_URL}/register/token',
        json=payload,
        headers={
            'ApiSecret': conf_settings.PASSKEY_API_PRIVATE_KEY,
        }
    )
    resp.raise_for_status()
    return JsonResponse(resp.json())


@csrf_exempt
def verify_token(request):
    token = request.GET['token']

    payload = {'token': token}

    resp = requests.post(
        f'{conf_settings.PASSKEY_API_URL}/signin/verify',
        json=payload,
        headers={
            'ApiSecret': conf_settings.PASSKEY_API_PRIVATE_KEY,
        }
    )
    resp.raise_for_status()
    json_data = resp.json()

    user = User.objects.get(pk=json_data['userId'])
    context = {"loggedin": True}
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
            raise ImproperLogin(
                "User could not be logged in. E101"
            )
        else:
            if user.is_active:
                login_user(request, user, backend='django.contrib.auth.backends.ModelBackend')
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
        context['loggedin'] = True
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
