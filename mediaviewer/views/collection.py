import itertools
from django.shortcuts import render, get_object_or_404

from mediaviewer.models import Movie, TV, Collection
from mediaviewer.models.sitegreeting import SiteGreeting
from mediaviewer.utils import logAccessInfo
from mediaviewer.views.views_utils import setSiteWideContext


@logAccessInfo
def collection(request, pk):
    siteGreeting = SiteGreeting.latestSiteGreeting()
    context = {}
    context["greeting"] = (
        siteGreeting and siteGreeting.greeting or "Check out the new downloads!"
    )
    context["active_page"] = "collections"
    collection = get_object_or_404(Collection, pk=pk)
    movies = Movie.objects.filter(collections=pk)
    tv_shows = TV.objects.filter(collections=pk)
    media = [x for x in itertools.chain(movies, tv_shows)]
    media = sorted(media, key=lambda x: x.name)
    context["media"] = media
    context["title"] = f"Collections: {collection.name}"
    setSiteWideContext(context, request, includeMessages=True)

    return render(request, "mediaviewer/collections.html", context)
