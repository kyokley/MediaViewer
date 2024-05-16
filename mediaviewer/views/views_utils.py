from mediaviewer.models import Genre, Collection
from mediaviewer.models.donation_site import DonationSite
from mediaviewer.models.message import LAST_WATCHED, REGULAR, Message
from mediaviewer.models.usersettings import FILENAME_SORT, UserSettings
from mediaviewer.models.waiterstatus import WaiterStatus


def setSiteWideContext(context, request, includeMessages=False):
    context["theme"] = request.session.get("theme", UserSettings.DARK)
    user = request.user
    if user.is_authenticated:
        settings = user.settings()
        context["loggedin"] = True
        context["user"] = user
        context["default_sort"] = settings and settings.default_sort or FILENAME_SORT

        if includeMessages:
            for message in Message.getMessagesForUser(
                request.user, message_type=REGULAR
            ):
                Message.add_message(
                    request, message.level, message.body, extra_tags=str(message.id)
                )

            for message in Message.getMessagesForUser(
                request.user, message_type=LAST_WATCHED
            ):
                Message.add_message(
                    request,
                    message.level,
                    message.body,
                    extra_tags=str(message.id) + " last_watched",
                )

        context["movie_genres"] = Genre.objects.get_movie_genres()
        context["tv_genres"] = Genre.objects.get_tv_genres()

        context["theme"] = settings.theme if settings else UserSettings.DARK
        context["collections"] = Collection.objects.all()
    else:
        context["loggedin"] = False

    context["is_staff"] = user.is_staff and "true" or "false"

    donation_site = DonationSite.objects.random()
    if donation_site:
        context["donation_site_name"] = donation_site.site_name
        context["donation_site_url"] = donation_site.url
    else:
        context["donation_site_name"] = ""
        context["donation_site_url"] = ""

    getLastWaiterStatus(context)


def getLastWaiterStatus(context):
    lastStatus = WaiterStatus.getLastStatus()
    context["waiterstatus"] = lastStatus and lastStatus.status or False
    context["waiterfailurereason"] = lastStatus and lastStatus.failureReason or ""
