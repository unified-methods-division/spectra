from rest_framework.generics import ListAPIView

from .models import TrendSnapshot
from .serializers import TrendSnapshotSerializer


class SnapshotListView(ListAPIView):
    serializer_class = TrendSnapshotSerializer

    def get_queryset(self):
        qs = TrendSnapshot.objects.filter(tenant=self.request.tenant).order_by(
            "snapshot_date"
        )
        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")
        if start:
            qs = qs.filter(snapshot_date__gte=start)
        if end:
            qs = qs.filter(snapshot_date__lte=end)
        return qs
