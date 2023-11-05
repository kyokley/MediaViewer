import json

from django.http import HttpResponse
from mediaviewer.models.sitegreeting import SiteGreeting
from django.shortcuts import render
from mediaviewer.utils import logAccessInfo
from mediaviewer.views.views_utils import setSiteWideContext
from django.conf import settings

from mediaviewer.log import log
from mediaviewer.models import MediaFile


@logAccessInfo
def home(request):
    siteGreeting = SiteGreeting.latestSiteGreeting()
    context = {}
    context["greeting"] = (
        siteGreeting and siteGreeting.greeting or "Check out the new downloads!"
    )
    context["active_page"] = "home"
    files = MediaFile.objects.most_recent_media()
    context["files"] = files
    context["title"] = "Home"
    setSiteWideContext(context, request, includeMessages=True)

    return render(request, "mediaviewer/home.html", context)


@logAccessInfo
def ajaxrunscraper(request):
    log.info("Running scraper")
    response = {"errmsg": ""}
    try:
        if request.user.is_staff:
            # WIP: Need to figure out what to do here
            # File.inferAllScrapers()
            pass
    except Exception as e:
        if settings.DEBUG:
            response["errmsg"] = str(e)
        else:
            response["errmsg"] = "An error has occurred"
    return HttpResponse(json.dumps(response), content_type="application/javascript")
