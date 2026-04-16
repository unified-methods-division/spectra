from rest_framework import serializers

from themes.models import Theme


class ThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theme
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "source",
            "item_count",
            "first_seen_at",
            "created_at",
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if hasattr(instance, "live_item_count"):
            data["item_count"] = instance.live_item_count
        return data
