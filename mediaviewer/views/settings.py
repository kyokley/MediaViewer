from datetime import datetime as dateObj

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.utils.timezone import utc

from mediaviewer.log import log
from mediaviewer.models.sitegreeting import SiteGreeting
from mediaviewer.models.usersettings import FILENAME_SORT, UserSettings
from mediaviewer.utils import logAccessInfo
from mediaviewer.views.views_utils import setSiteWideContext


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def settings(request):
    siteGreeting = SiteGreeting.latestSiteGreeting()
    context = {
        "greeting": (
            siteGreeting and siteGreeting.greeting or "Check out the new downloads!"
        ),
    }
    context["active_page"] = "settings"
    user = request.user
    settings = user.settings()
    context["title"] = "Settings"
    context["binge_mode"] = settings.binge_mode
    context["jump_to_last"] = settings.jump_to_last_watched
    context["light_theme_option"] = UserSettings.LIGHT
    context["dark_theme_option"] = UserSettings.DARK
    context["selected_theme"] = settings.theme

    context["email"] = user.email
    if not user.email:
        context["display_missing_email_modal"] = True
    else:
        context["display_missing_email_modal"] = False

    setSiteWideContext(context, request, includeMessages=False)

    return render(request, "mediaviewer/settings.html", context)


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def submitsettings(request):
    context = {"successful": True}
    context["active_page"] = "submitsettings"
    setSiteWideContext(context, request)

    default_sort = request.POST.get("default_sort")
    if not default_sort:
        default_sort = FILENAME_SORT

    binge_mode = request.POST.get("binge_mode")
    if not binge_mode:
        binge_mode = False
    else:
        binge_mode = binge_mode == "true"

    jump_to_last = request.POST.get("jump_to_last")
    if not jump_to_last:
        jump_to_last = False
    else:
        jump_to_last = jump_to_last == "true"

    theme = request.POST.get("theme", context.get("theme", UserSettings.DARK))

    user = request.user
    settings = user.settings()

    changed = (
        settings.default_sort != default_sort
        or settings.binge_mode != binge_mode
        or settings.jump_to_last_watched != jump_to_last
    )

    settings.binge_mode = binge_mode
    settings.jump_to_last_watched = jump_to_last
    settings.default_sort = default_sort
    settings.theme = theme
    context["theme"] = theme
    request.session["theme"] = theme

    user.email = request.POST.get("email_field", user.email)
    context["default_sort"] = settings.default_sort

    if changed:
        settings.dateedited = dateObj.now(utc)

    settings.save()
    user.save()
    return render(request, "mediaviewer/settingsresults.html", context)


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def submitnewuser(request):
    user = request.user
    context = {"successful": True}
    context["active_page"] = "submitnewuser"
    setSiteWideContext(context, request)

    new_user_email = request.POST.get("new_user_email")
    if user.is_staff:
        if new_user_email:
            try:
                UserSettings.new(
                    new_user_email,
                    new_user_email,
                    can_download=True,
                )
            except ValidationError as e:
                context["successful"] = False
                context["errMsg"] = e.message
            except Exception as e:
                context["successful"] = False
                context["errMsg"] = str(e)
    else:
        log.error("User is not a staffer!")
        context["errMsg"] = "Unauthorized access attempted"
        context["successful"] = False
    return render(request, "mediaviewer/settingsresults.html", context)
