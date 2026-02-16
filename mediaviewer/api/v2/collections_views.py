"""Collection views for API v2"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from mediaviewer.models.collection import Collection

from .collection_serializers import CollectionSerializer


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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def collection_items(request, collection_id):
    """
    GET /api/v2/collections/{id}/items/ - List items in collection
    """
    if not Collection.objects.filter(pk=collection_id).exists():
        return Response(
            {
                "error": {
                    "code": "COLLECTION_NOT_FOUND",
                    "message": f"Collection with id {collection_id} not found",
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        # Get items from collection
        # The structure depends on how collections relate to movies/tv
        # This is a placeholder implementation
        items = []

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
