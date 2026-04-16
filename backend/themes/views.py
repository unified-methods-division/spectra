from collections import Counter

from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from ingestion.models import FeedbackItem
from themes.models import Theme
from themes.serializers import ThemeSerializer
from themes.tasks import discover_themes_for_tenant


def _feedback_theme_slug_counts(*, tenant_id):
    """Count feedback rows per theme slug (same semantics as themes__contains=[slug])."""
    counts: Counter[str] = Counter()
    qs = (
        FeedbackItem.objects.filter(tenant_id=tenant_id)
        .exclude(themes__isnull=True)
        .values_list("themes", flat=True)
    )
    for theme_list in qs.iterator(chunk_size=2000):
        if not theme_list:
            continue
        for slug in set(theme_list):
            counts[slug] += 1
    return counts


class ThemeListView(ListAPIView):
    serializer_class = ThemeSerializer

    def get_queryset(self):
        return Theme.objects.filter(tenant=self.request.tenant).order_by("slug")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        slug_counts = _feedback_theme_slug_counts(tenant_id=request.tenant.id)
        rows = list(queryset)
        for row in rows:
            row.live_item_count = slug_counts.get(row.slug, 0)
        rows.sort(key=lambda t: (-t.live_item_count, t.slug))
        serializer = self.get_serializer(rows, many=True)
        return Response(serializer.data)


class TriggerDiscoveryView(APIView):
    def post(self, request):
        discover_themes_for_tenant.delay(str(request.tenant.id))
        return Response({"status": "discovery started"}, status=status.HTTP_202_ACCEPTED)
