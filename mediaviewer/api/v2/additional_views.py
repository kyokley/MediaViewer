"""Additional views for API v2 (requests, video progress, comments, search)"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from mediaviewer.models.request import Request
from mediaviewer.models.videoprogress import VideoProgress
from mediaviewer.models.comment import Comment
from mediaviewer.models.movie import Movie
from mediaviewer.models.tv import TV
from .additional_serializers import (
    RequestSerializer,
    VideoProgressSerializer,
    CommentSerializer,
)


# ============================================================================
# REQUEST ENDPOINTS
# ============================================================================


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def list_requests(request):
    """
    GET /api/v2/requests/ - List all media requests
    POST /api/v2/requests/ - Create new media request
    """
    if request.method == "GET":
        try:
            requests_qs = Request.objects.all().order_by("-datecreated")

            # Handle pagination
            limit = min(int(request.query_params.get("limit", 50)), 500)
            offset = int(request.query_params.get("offset", 0))

            total_count = requests_qs.count()
            requests_qs = requests_qs[offset : offset + limit]

            serializer = RequestSerializer(requests_qs, many=True)
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
                        "message": "Failed to fetch requests",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    elif request.method == "POST":
        try:
            data = request.data.copy()
            data["user"] = request.user.id

            serializer = RequestSerializer(data=data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(
                {
                    "error": {
                        "code": "INVALID_DATA",
                        "message": "Invalid request data",
                        "details": serializer.errors,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {
                    "error": {
                        "code": "CREATE_ERROR",
                        "message": "Failed to create request",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def request_detail(request, request_id):
    """
    GET /api/v2/requests/{id}/ - Get request details
    PUT /api/v2/requests/{id}/ - Update request
    DELETE /api/v2/requests/{id}/ - Delete request
    """
    try:
        req_obj = Request.objects.get(pk=request_id)
    except Request.DoesNotExist:
        return Response(
            {
                "error": {
                    "code": "REQUEST_NOT_FOUND",
                    "message": f"Request with id {request_id} not found",
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        try:
            serializer = RequestSerializer(req_obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {
                    "error": {
                        "code": "FETCH_ERROR",
                        "message": "Failed to fetch request",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    elif request.method == "PUT":
        try:
            serializer = RequestSerializer(req_obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(
                {
                    "error": {
                        "code": "INVALID_DATA",
                        "message": "Invalid request data",
                        "details": serializer.errors,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {
                    "error": {
                        "code": "UPDATE_ERROR",
                        "message": "Failed to update request",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    elif request.method == "DELETE":
        try:
            req_obj.delete()
            return Response(
                {"message": "Request deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            return Response(
                {
                    "error": {
                        "code": "DELETE_ERROR",
                        "message": "Failed to delete request",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ============================================================================
# VIDEO PROGRESS ENDPOINTS
# ============================================================================


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def list_video_progress(request):
    """
    GET /api/v2/video-progress/ - List user's video progress
    POST /api/v2/video-progress/ - Save video progress
    """
    if request.method == "GET":
        try:
            progress = VideoProgress.objects.filter(user=request.user).order_by(
                "-date_edited"
            )

            # Handle pagination
            limit = min(int(request.query_params.get("limit", 50)), 500)
            offset = int(request.query_params.get("offset", 0))

            total_count = progress.count()
            progress = progress[offset : offset + limit]

            serializer = VideoProgressSerializer(progress, many=True)
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
                        "message": "Failed to fetch video progress",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    elif request.method == "POST":
        try:
            data = request.data.copy()
            data["user"] = request.user.id

            # Update existing or create new
            hashed_filename = data.get("hashed_filename")
            if hashed_filename:
                try:
                    progress = VideoProgress.objects.get(
                        user=request.user, hashed_filename=hashed_filename
                    )
                    serializer = VideoProgressSerializer(
                        progress, data=data, partial=True
                    )
                except VideoProgress.DoesNotExist:
                    serializer = VideoProgressSerializer(data=data)

                if serializer.is_valid():
                    serializer.save(user=request.user)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)

                return Response(
                    {
                        "error": {
                            "code": "INVALID_DATA",
                            "message": "Invalid progress data",
                            "details": serializer.errors,
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return Response(
                    {
                        "error": {
                            "code": "MISSING_FIELD",
                            "message": "hashed_filename is required",
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            return Response(
                {
                    "error": {
                        "code": "CREATE_ERROR",
                        "message": "Failed to save progress",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_video_progress(request, hashed_filename):
    """
    DELETE /api/v2/video-progress/{hashed_filename}/ - Delete video progress
    """
    try:
        VideoProgress.objects.destroy(request.user, hashed_filename)
        return Response(
            {"message": "Progress deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )
    except Exception as e:
        return Response(
            {
                "error": {
                    "code": "DELETE_ERROR",
                    "message": "Failed to delete progress",
                    "details": str(e),
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ============================================================================
# COMMENT ENDPOINTS
# ============================================================================


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def list_comments(request):
    """
    GET /api/v2/comments/ - List user's comments
    POST /api/v2/comments/ - Create new comment
    """
    if request.method == "GET":
        try:
            comments = Comment.objects.filter(user=request.user).order_by(
                "-date_created"
            )

            # Handle pagination
            limit = min(int(request.query_params.get("limit", 50)), 500)
            offset = int(request.query_params.get("offset", 0))

            total_count = comments.count()
            comments = comments[offset : offset + limit]

            serializer = CommentSerializer(comments, many=True)
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
                        "message": "Failed to fetch comments",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    elif request.method == "POST":
        try:
            data = request.data.copy()
            data["user"] = request.user.id

            serializer = CommentSerializer(data=data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(
                {
                    "error": {
                        "code": "INVALID_DATA",
                        "message": "Invalid comment data",
                        "details": serializer.errors,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {
                    "error": {
                        "code": "CREATE_ERROR",
                        "message": "Failed to create comment",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def comment_detail(request, comment_id):
    """
    GET /api/v2/comments/{id}/ - Get comment details
    PUT /api/v2/comments/{id}/ - Update comment
    DELETE /api/v2/comments/{id}/ - Delete comment
    """
    try:
        comment = Comment.objects.get(pk=comment_id, user=request.user)
    except Comment.DoesNotExist:
        return Response(
            {
                "error": {
                    "code": "COMMENT_NOT_FOUND",
                    "message": f"Comment with id {comment_id} not found",
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        try:
            serializer = CommentSerializer(comment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {
                    "error": {
                        "code": "FETCH_ERROR",
                        "message": "Failed to fetch comment",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    elif request.method == "PUT":
        try:
            serializer = CommentSerializer(comment, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(
                {
                    "error": {
                        "code": "INVALID_DATA",
                        "message": "Invalid comment data",
                        "details": serializer.errors,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {
                    "error": {
                        "code": "UPDATE_ERROR",
                        "message": "Failed to update comment",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    elif request.method == "DELETE":
        try:
            comment.delete()
            return Response(
                {"message": "Comment deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            return Response(
                {
                    "error": {
                        "code": "DELETE_ERROR",
                        "message": "Failed to delete comment",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ============================================================================
# SEARCH ENDPOINT
# ============================================================================


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search(request):
    """
    GET /api/v2/search/ - Search across all media
    Query parameters:
    - q: Search query (required)
    - type: Filter by type ('movie', 'tv', or empty for all)
    - limit: Number of results (default: 20)
    """
    try:
        query = request.query_params.get("q", "").strip()
        if not query or len(query) < 2:
            return Response(
                {
                    "error": {
                        "code": "INVALID_QUERY",
                        "message": "Search query must be at least 2 characters",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        limit = min(int(request.query_params.get("limit", 20)), 100)
        search_type = request.query_params.get("type", "").strip().lower()

        results = {
            "movies": [],
            "tv": [],
            "genres": [],
        }

        # Search movies
        if search_type in ("", "movie"):
            from .media_serializers import MovieSerializer

            movies = Movie.objects.filter(name__icontains=query)[:limit]
            results["movies"] = MovieSerializer(
                movies, many=True, context={"request": request}
            ).data

        # Search TV shows
        if search_type in ("", "tv"):
            from .media_serializers import TVSerializer

            tv_shows = TV.objects.filter(name__icontains=query)[:limit]
            results["tv"] = TVSerializer(
                tv_shows, many=True, context={"request": request}
            ).data

        return Response(
            {
                "data": results,
                "query": query,
                "type_filter": search_type or "all",
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {
                "error": {
                    "code": "SEARCH_ERROR",
                    "message": "Search failed",
                    "details": str(e),
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
