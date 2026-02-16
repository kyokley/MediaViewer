"""Media views for API v2"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from mediaviewer.models.movie import Movie
from mediaviewer.models.tv import TV
from mediaviewer.models.genre import Genre
from .media_serializers import MovieSerializer, TVSerializer, GenreSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_movies(request):
    """
    GET /api/v2/movies/ - List all movies
    Query parameters:
    - search: Search by movie name
    - limit: Number of results (default: 50)
    - offset: Pagination offset (default: 0)
    """
    try:
        movies = Movie.objects.all()

        # Handle search
        search_query = request.query_params.get("search", "").strip()
        if search_query:
            movies = movies.filter(name__icontains=search_query)

        # Handle pagination
        limit = min(int(request.query_params.get("limit", 50)), 500)
        offset = int(request.query_params.get("offset", 0))

        total_count = movies.count()
        movies = movies[offset : offset + limit]

        serializer = MovieSerializer(movies, many=True, context={"request": request})

        return Response(
            {
                "data": serializer.data,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                },
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {
                "error": {
                    "code": "FETCH_ERROR",
                    "message": "Failed to fetch movies",
                    "details": str(e),
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def movie_detail(request, movie_id):
    """
    GET /api/v2/movies/{id}/ - Get movie details
    """
    try:
        movie = Movie.objects.get(pk=movie_id)
        serializer = MovieSerializer(movie, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Movie.DoesNotExist:
        return Response(
            {
                "error": {
                    "code": "MOVIE_NOT_FOUND",
                    "message": f"Movie with id {movie_id} not found",
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {
                "error": {
                    "code": "FETCH_ERROR",
                    "message": "Failed to fetch movie",
                    "details": str(e),
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_tv(request):
    """
    GET /api/v2/tv/ - List all TV shows
    Query parameters:
    - search: Search by TV name
    - limit: Number of results (default: 50)
    - offset: Pagination offset (default: 0)
    """
    try:
        tv_shows = TV.objects.all()

        # Handle search
        search_query = request.query_params.get("search", "").strip()
        if search_query:
            tv_shows = tv_shows.filter(name__icontains=search_query)

        # Handle pagination
        limit = min(int(request.query_params.get("limit", 50)), 500)
        offset = int(request.query_params.get("offset", 0))

        total_count = tv_shows.count()
        tv_shows = tv_shows[offset : offset + limit]

        serializer = TVSerializer(tv_shows, many=True, context={"request": request})

        return Response(
            {
                "data": serializer.data,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                },
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {
                "error": {
                    "code": "FETCH_ERROR",
                    "message": "Failed to fetch TV shows",
                    "details": str(e),
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tv_detail(request, tv_id):
    """
    GET /api/v2/tv/{id}/ - Get TV show details
    """
    try:
        tv_show = TV.objects.get(pk=tv_id)
        serializer = TVSerializer(tv_show, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    except TV.DoesNotExist:
        return Response(
            {
                "error": {
                    "code": "TV_NOT_FOUND",
                    "message": f"TV show with id {tv_id} not found",
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {
                "error": {
                    "code": "FETCH_ERROR",
                    "message": "Failed to fetch TV show",
                    "details": str(e),
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_genres(request):
    """
    GET /api/v2/genres/ - List all genres
    Query parameters:
    - media_type: Filter by 'movie' or 'tv'
    - limit: Number of results (default: 50)
    """
    try:
        genres = Genre.objects.all()

        # Handle media type filter
        media_type = request.query_params.get("media_type", "").strip().lower()
        if media_type == "movie":
            # Only genres with movies
            genres = genres.filter(poster__movie__isnull=False).distinct()
        elif media_type == "tv":
            # Only genres with TV shows
            genres = genres.filter(poster__tv__isnull=False).distinct()

        # Handle pagination
        limit = min(int(request.query_params.get("limit", 50)), 500)
        offset = int(request.query_params.get("offset", 0))

        total_count = genres.count()
        genres = genres.order_by("genre")[offset : offset + limit]

        serializer = GenreSerializer(genres, many=True)

        return Response(
            {
                "data": serializer.data,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                },
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {
                "error": {
                    "code": "FETCH_ERROR",
                    "message": "Failed to fetch genres",
                    "details": str(e),
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
