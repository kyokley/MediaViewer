from mediaviewer.models.waiterstatus import WaiterStatus
from mediaviewer.models.file import File
from mediaviewer.models.path import Path
from mediaviewer.models.usersettings import FILENAME_SORT
from mediaviewer.models.message import (Message,
                                        REGULAR,
                                        LAST_WATCHED,
                                        )
from mediaviewer.models.donation_site import DonationSite


def setSiteWideContext(context, request, includeMessages=False):
    user = request.user
    if user.is_authenticated:
        settings = user.settings()
        context['loggedin'] = True
        context['user'] = user
        context['default_sort'] = (settings and
                                   settings.default_sort or
                                   FILENAME_SORT)
        donation_site = DonationSite.objects.random()
        if donation_site:
            context['donation_site_name'] = donation_site.site_name
            context['donation_site_url'] = donation_site.url
        else:
            context['donation_site_name'] = ''
            context['donation_site_url'] = ''

        if includeMessages:
            for message in Message.getMessagesForUser(request.user,
                                                      message_type=REGULAR):
                Message.add_message(request,
                                    message.level,
                                    message.body,
                                    extra_tags=str(message.id))

            for message in Message.getMessagesForUser(
                    request.user,
                    message_type=LAST_WATCHED):
                Message.add_message(
                        request,
                        message.level,
                        message.body,
                        extra_tags=str(message.id) + ' last_watched')

        context['movie_genres'] = File.get_movie_genres()
        context['tv_genres'] = Path.get_tv_genres()
    else:
        context['loggedin'] = False

    context['is_staff'] = user.is_staff and 'true' or 'false'
    getLastWaiterStatus(context)


def getLastWaiterStatus(context):
    lastStatus = WaiterStatus.getLastStatus()
    context['waiterstatus'] = lastStatus and lastStatus.status or False
    context['waiterfailurereason'] = (lastStatus and
                                      lastStatus.failureReason or
                                      '')
