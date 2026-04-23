from django.urls import path

from .views import SnapshotListView, alert_acknowledge, alerts_list, dashboard_summary

urlpatterns = [
    path("snapshots/", SnapshotListView.as_view(), name="trend-snapshots-list"),
    path("dashboard/summary/", dashboard_summary, name="dashboard-summary"),
    path("alerts/", alerts_list, name="alerts-list"),
    path("alerts/<uuid:alert_id>/ack/", alert_acknowledge, name="alert-ack"),
]
