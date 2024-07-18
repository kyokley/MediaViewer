import itertools
import random
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from mediaviewer.models import Movie, TV, Collection
from mediaviewer.models.sitegreeting import SiteGreeting
from mediaviewer.utils import logAccessInfo
from mediaviewer.views.views_utils import setSiteWideContext


rand = random.SystemRandom()


@login_required(login_url="/mediaviewer/login/")
@logAccessInfo
def collection(request, pk):
    siteGreeting = SiteGreeting.latestSiteGreeting()
    context = {}
    context["greeting"] = (
        siteGreeting and siteGreeting.greeting or "Check out the new downloads!"
    )
    context["active_page"] = "collections"
    collection = get_object_or_404(Collection, pk=pk)
    movies = Movie.objects.filter(collections=pk).select_related('_poster')
    tv_shows = TV.objects.filter(collections=pk).select_related('_poster')
    medias = [x for x in itertools.chain(movies, tv_shows)]
    medias = sorted(medias, key=lambda x: x.name)
    context["medias"] = medias
    context["title"] = f"Collections: {collection.name}"

    carousel_files = [x for x in medias if x._poster.image]
    rand.shuffle(carousel_files)
    context["carousel_files"] = carousel_files
    setSiteWideContext(context, request, includeMessages=True)

    return render(request, "mediaviewer/collections.html", context)
