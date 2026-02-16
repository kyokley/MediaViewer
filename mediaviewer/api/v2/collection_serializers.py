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
            # Collections have a many-to-many relationship with movies/tv
            # The exact relationship depends on the implementation
            return 0  # Placeholder - update based on actual relationship
        except Exception:
            return 0
