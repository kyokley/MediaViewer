"""Collection serializers for API v2"""

from rest_framework import serializers
from mediaviewer.models.collection import Collection


class CollectionSerializer(serializers.ModelSerializer):
    """Serialize Collection model"""

    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = ["id", "name", "item_count"]
        read_only_fields = ["id", "item_count"]

    def get_item_count(self, obj):
        """Get the number of items in the collection"""
        try:
            # Count movies and TV shows in this collection
            movie_count = obj.movie_set.count()
            tv_count = obj.tv_set.count()
            return movie_count + tv_count
        except Exception:
            return 0
