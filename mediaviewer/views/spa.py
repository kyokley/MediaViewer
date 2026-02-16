from django.conf import settings
from django.http import FileResponse
from django.views.decorators.csrf import csrf_exempt
from pathlib import Path


@csrf_exempt
def serve_spa(request):
    """
    Serve the React SPA index.html for all non-API routes.
    This allows React Router to handle client-side routing.
    """
    # The React build output is typically in frontend/dist/index.html
    spa_index_path = Path(settings.BASE_DIR) / "frontend" / "dist" / "index.html"

    if spa_index_path.exists():
        return FileResponse(open(spa_index_path, "rb"), content_type="text/html")

    # Fallback if dist doesn't exist (during development)
    return FileResponse(
        open(Path(settings.BASE_DIR) / "frontend" / "index.html", "rb"),
        content_type="text/html",
    )
