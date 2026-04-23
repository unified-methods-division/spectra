from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    FeedbackItemViewSet,
    IngestionTaskStatusView,
    RoutingConfigView,
    SourceViewSet,
    UploadFeedbackFileView,
    WebhookFeedbackView,
)

router = DefaultRouter()
router.register("sources", SourceViewSet, basename="sources")
router.register("feedback-items", FeedbackItemViewSet, basename="feedback-items")

urlpatterns = [
    path(
        "sources/<uuid:source_id>/uploads/",
        UploadFeedbackFileView.as_view(),
        name="upload-feedback-file",
    ),
    path(
        "uploads/tasks/<str:task_id>/",
        IngestionTaskStatusView.as_view(),
        name="ingestion-task-status",
    ),
    path(
        "sources/<uuid:source_id>/webhook/",
        WebhookFeedbackView.as_view(),
        name="webhook-feedback",
    ),
    path(
        "sources/<uuid:source_id>/routing-config/",
        RoutingConfigView.as_view(),
        name="routing-config",
    ),
    path("", include(router.urls)),
]
