"""Collection views for API v2"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from mediaviewer.models.collection import Collection
from mediaviewer.models.movie import Movie
from mediaviewer.models.tv import TV

from .collection_serializers import CollectionSerializer
from .media_serializers import MovieSerializer, TVSerializer


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def list_collections(request):
    """
    GET /api/v2/collections/ - List all collections
    POST /api/v2/collections/ - Create a new collection
    """
    if request.method == "GET":
        try:
            collections = Collection.objects.all()

            # Handle pagination
            limit = min(int(request.query_params.get("limit", 50)), 500)
            offset = int(request.query_params.get("offset", 0))

            total_count = collections.count()
            collections = collections[offset : offset + limit]

            serializer = CollectionSerializer(collections, many=True)

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
                        "message": "Failed to fetch collections",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    elif request.method == "POST":
        try:
            serializer = CollectionSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(
                {
                    "error": {
                        "code": "INVALID_DATA",
                        "message": "Invalid collection data",
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
                        "message": "Failed to create collection",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def collection_detail(request, collection_id):
    """
    GET /api/v2/collections/{id}/ - Get collection details
    PUT /api/v2/collections/{id}/ - Update collection
    DELETE /api/v2/collections/{id}/ - Delete collection
    """
    try:
        collection = Collection.objects.get(pk=collection_id)
    except Collection.DoesNotExist:
        return Response(
            {
                "error": {
                    "code": "COLLECTION_NOT_FOUND",
                    "message": f"Collection with id {collection_id} not found",
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        try:
            serializer = CollectionSerializer(collection)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {
                    "error": {
                        "code": "FETCH_ERROR",
                        "message": "Failed to fetch collection",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    elif request.method == "PUT":
        try:
            serializer = CollectionSerializer(
                collection, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(
                {
                    "error": {
                        "code": "INVALID_DATA",
                        "message": "Invalid collection data",
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
                        "message": "Failed to update collection",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    elif request.method == "DELETE":
        try:
            collection.delete()
            return Response(
                {"message": "Collection deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            return Response(
                {
                    "error": {
                        "code": "DELETE_ERROR",
                        "message": "Failed to delete collection",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["GET", "POST", "DELETE"])
@permission_classes([IsAuthenticated])
def collection_items(request, collection_id):
    """
    GET /api/v2/collections/{id}/items/ - List items in collection
    POST /api/v2/collections/{id}/items/ - Add item to collection
    DELETE /api/v2/collections/{id}/items/ - Remove item from collection
    """
    # Check if collection exists
    try:
        collection = Collection.objects.get(pk=collection_id)
    except Collection.DoesNotExist:
        return Response(
            {
                "error": {
                    "code": "COLLECTION_NOT_FOUND",
                    "message": f"Collection with id {collection_id} not found",
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        try:
            # Get movies and TV shows in this collection
            movies = Movie.objects.filter(collections=collection)
            tv_shows = TV.objects.filter(collections=collection)

            # Serialize the items with media_type indicator
            movie_data = MovieSerializer(
                movies, many=True, context={"request": request}
            ).data
            tv_data = TVSerializer(
                tv_shows, many=True, context={"request": request}
            ).data

            # Add media_type to each item
            for item in movie_data:
                item["media_type"] = "movie"
            for item in tv_data:
                item["media_type"] = "tv"

            # Combine and return
            items = list(movie_data) + list(tv_data)

            return Response(
                {
                    "data": items,
                    "pagination": {
                        "total": len(items),
                        "limit": len(items),
                        "offset": 0,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    "error": {
                        "code": "FETCH_ERROR",
                        "message": "Failed to fetch collection items",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    elif request.method == "POST":
        try:
            # Get media_id and media_type from request body
            media_id = request.data.get("media_id")
            media_type = request.data.get("media_type", "").lower()

            if not media_id:
                return Response(
                    {
                        "error": {
                            "code": "INVALID_DATA",
                            "message": "media_id is required",
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if media_type not in ["movie", "tv"]:
                return Response(
                    {
                        "error": {
                            "code": "INVALID_DATA",
                            "message": "media_type must be 'movie' or 'tv'",
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get the media item and add it to the collection
            if media_type == "movie":
                try:
                    media_item = Movie.objects.get(pk=media_id)
                except Movie.DoesNotExist:
                    return Response(
                        {
                            "error": {
                                "code": "MOVIE_NOT_FOUND",
                                "message": f"Movie with id {media_id} not found",
                            }
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:  # tv
                try:
                    media_item = TV.objects.get(pk=media_id)
                except TV.DoesNotExist:
                    return Response(
                        {
                            "error": {
                                "code": "TV_NOT_FOUND",
                                "message": f"TV show with id {media_id} not found",
                            }
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )

            # Add the media item to the collection
            media_item.collections.add(collection)

            return Response(
                {
                    "message": f"{media_type.capitalize()} added to collection successfully",
                    "collection_id": collection_id,
                    "media_id": media_id,
                    "media_type": media_type,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {
                    "error": {
                        "code": "ADD_ERROR",
                        "message": "Failed to add item to collection",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    elif request.method == "DELETE":
        try:
            # Get media_id and media_type from query params
            media_id = request.query_params.get("media_id")
            media_type = request.query_params.get("media_type", "").lower()

            if not media_id:
                return Response(
                    {
                        "error": {
                            "code": "INVALID_DATA",
                            "message": "media_id query parameter is required",
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if media_type not in ["movie", "tv"]:
                return Response(
                    {
                        "error": {
                            "code": "INVALID_DATA",
                            "message": "media_type query parameter must be 'movie' or 'tv'",
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get the media item and remove it from the collection
            if media_type == "movie":
                try:
                    media_item = Movie.objects.get(pk=media_id)
                except Movie.DoesNotExist:
                    return Response(
                        {
                            "error": {
                                "code": "MOVIE_NOT_FOUND",
                                "message": f"Movie with id {media_id} not found",
                            }
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:  # tv
                try:
                    media_item = TV.objects.get(pk=media_id)
                except TV.DoesNotExist:
                    return Response(
                        {
                            "error": {
                                "code": "TV_NOT_FOUND",
                                "message": f"TV show with id {media_id} not found",
                            }
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )

            # Remove the media item from the collection
            media_item.collections.remove(collection)

            return Response(
                {
                    "message": f"{media_type.capitalize()} removed from collection successfully"
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    "error": {
                        "code": "REMOVE_ERROR",
                        "message": "Failed to remove item from collection",
                        "details": str(e),
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
