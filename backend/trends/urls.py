from django.urls import path

from .views import SnapshotListView

urlpatterns = [
    path("snapshots/", SnapshotListView.as_view(), name="trend-snapshots-list"),
]
