from django.urls import reverse
from django.shortcuts import redirect
from urllib.parse import quote_plus, urlencode
from django.conf import settings as conf_settings


def logout(request):
    request.session.clear()

    return redirect(
        f"https://{conf_settings.AUTH0_DOMAIN}/v2/logout?"
        + urlencode(
            {
                "returnTo": request.build_absolute_uri(reverse("mediaviewer:home")),
                "client_id": conf_settings.AUTH0_CLIENT_ID,
            },
            quote_via=quote_plus,
        ),
    )
