import random
from django.shortcuts import render

from mediaviewer.models import MediaFile
from mediaviewer.models.sitegreeting import SiteGreeting
from mediaviewer.utils import logAccessInfo
from mediaviewer.views.views_utils import setSiteWideContext


rand = random.SystemRandom()


@logAccessInfo
def home(request):
    siteGreeting = SiteGreeting.latestSiteGreeting()
    context = {}
    context["greeting"] = (
        siteGreeting and siteGreeting.greeting or "Check out the new downloads!"
    )
    context["active_page"] = "home"
    carousel_files = list(MediaFile.objects.most_recent_media())
    rand.shuffle(carousel_files)
    context["carousel_files"] = carousel_files
    context["title"] = "Home"
    setSiteWideContext(context, request, includeMessages=True)

    return render(request, "mediaviewer/home.html", context)
