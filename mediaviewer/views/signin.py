from django.urls import reverse
from mediaviewer.models.sitegreeting import SiteGreeting
from django.shortcuts import render, redirect
from mediaviewer.views.views_utils import setSiteWideContext
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_login_failed
from mediaviewer.models.loginevent import LoginEvent
from django.http import HttpResponseRedirect
from django.conf import settings as conf_settings
from mediaviewer.utils import logAccessInfo
from mediaviewer.models.usersettings import (
    ImproperLogin,
    case_insensitive_authenticate,
)
from authlib.integrations.django_client import OAuth


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
                        login(request, user)
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
        request, request.build_absolute_uri(reverse("callback"))
    )


def callback(request):
    token = oauth.auth0.authorize_access_token(request)
    request.session["user"] = token
    return redirect(request.build_absolute_uri(reverse("index")))
