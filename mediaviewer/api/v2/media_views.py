"""Media views for API v2"""

from django.db import models
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from mediaviewer.models.movie import Movie
from mediaviewer.models.tv import TV
from mediaviewer.models.genre import Genre
from .media_serializers import (
    MovieSerializer,
    TVSerializer,
    GenreSerializer,
    EpisodeSerializer,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_movies(request):
    """
    GET /api/v2/movies/ - List all movies
    Query parameters:
    - search: Search by movie name
    - genre: Filter by genre ID
    - sort_by: Sort order - 'date_added' (default), 'name', 'release_date'
    - limit: Number of results (default: 50)
    - offset: Pagination offset (default: 0)
    """
    try:
        movies = Movie.objects.all()

        # Handle search
        search_query = request.query_params.get("search", "").strip()
        if search_query:
            movies = movies.filter(name__icontains=search_query)

        # Handle genre filter
        genre_id = request.query_params.get("genre", "").strip()
        if genre_id:
            movies = movies.filter(_poster__genres__id=genre_id)

        # Handle sorting
        sort_by = request.query_params.get("sort_by", "date_added").strip().lower()
        if sort_by == "date_added":
            movies = movies.order_by("-date_created")
        elif sort_by == "name":
            movies = movies.order_by("name")
        elif sort_by == "release_date":
            movies = movies.order_by("-release_date")
        else:
            # Default to most recently added
            movies = movies.order_by("-date_created")

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
    - genre: Filter by genre ID
    - sort_by: Sort order - 'date_added' (default), 'name', 'first_air_date'
    - limit: Number of results (default: 50)
    - offset: Pagination offset (default: 0)
    """
    try:
        tv_shows = TV.objects.all()

        # Handle search
        search_query = request.query_params.get("search", "").strip()
        if search_query:
            tv_shows = tv_shows.filter(name__icontains=search_query)

        # Handle genre filter
        genre_id = request.query_params.get("genre", "").strip()
        if genre_id:
            tv_shows = tv_shows.filter(_poster__genres__id=genre_id)

        # Handle sorting
        sort_by = request.query_params.get("sort_by", "date_added").strip().lower()
        if sort_by == "date_added":
            tv_shows = tv_shows.order_by("-date_created")
        elif sort_by == "name":
            tv_shows = tv_shows.order_by("name")
        elif sort_by == "first_air_date":
            tv_shows = tv_shows.order_by("-first_air_date")
        else:
            # Default to most recently added
            tv_shows = tv_shows.order_by("-date_created")

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
    - sort_by: Sort order - 'popularity' (default) or 'name'
    """
    try:
        # Handle media type filter and sorting
        media_type = request.query_params.get("media_type", "").strip().lower()
        sort_by = request.query_params.get("sort_by", "popularity").strip().lower()

        # Handle pagination
        limit = min(int(request.query_params.get("limit", 50)), 500)
        offset = int(request.query_params.get("offset", 0))

        if sort_by == "popularity":
            # Sort by popularity (count of associated movies/TV shows)
            if media_type == "movie":
                # Get genres with movie count, sorted by popularity
                genres = (
                    Genre.objects.filter(poster__movie__isnull=False)
                    .annotate(usage_count=models.Count("poster__movie", distinct=True))
                    .order_by("-usage_count", "genre")
                    .distinct()
                )
            elif media_type == "tv":
                # Get genres with TV show count, sorted by popularity
                genres = (
                    Genre.objects.filter(poster__tv__isnull=False)
                    .annotate(usage_count=models.Count("poster__tv", distinct=True))
                    .order_by("-usage_count", "genre")
                    .distinct()
                )
            else:
                # Get all genres with combined count
                genres = Genre.objects.annotate(
                    usage_count=models.Count("poster", distinct=True)
                ).order_by("-usage_count", "genre")
        else:
            # Sort alphabetically by name
            genres = Genre.objects.all()
            if media_type == "movie":
                genres = genres.filter(poster__movie__isnull=False).distinct()
            elif media_type == "tv":
                genres = genres.filter(poster__tv__isnull=False).distinct()
            genres = genres.order_by("genre")

        total_count = genres.count()
        genres = genres[offset : offset + limit]

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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_episodes(request, tv_id):
    """
    GET /api/v2/tv/{tv_id}/episodes/ - List all episodes for a TV show
    """
    try:
        # Check if TV show exists
        tv_show = TV.objects.get(pk=tv_id)

        # Get episodes using the TV model's episodes() method
        episodes = tv_show.episodes()

        # Serialize episodes
        serializer = EpisodeSerializer(
            episodes, many=True, context={"request": request}
        )

        # Group episodes by season
        episodes_by_season = {}
        for episode_data in serializer.data:
            season_num = episode_data.get("season")
            if season_num is not None:
                if season_num not in episodes_by_season:
                    episodes_by_season[season_num] = []
                episodes_by_season[season_num].append(episode_data)

        # Convert to sorted list of seasons
        seasons = [
            {
                "season_number": season_num,
                "episodes": sorted(
                    episodes_by_season[season_num], key=lambda x: x.get("episode", 0)
                ),
            }
            for season_num in sorted(episodes_by_season.keys())
        ]

        return Response(
            {
                "data": seasons,
                "total_episodes": len(serializer.data),
                "total_seasons": len(seasons),
            },
            status=status.HTTP_200_OK,
        )

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
                    "message": "Failed to fetch episodes",
                    "details": str(e),
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
