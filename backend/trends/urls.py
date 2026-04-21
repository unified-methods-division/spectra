from django.urls import path

from .views import SnapshotListView, dashboard_summary

urlpatterns = [
    path("snapshots/", SnapshotListView.as_view(), name="trend-snapshots-list"),
    path("dashboard/summary/", dashboard_summary, name="dashboard-summary"),
]
