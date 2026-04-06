from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    FeedbackItemViewSet,
    IngestionTaskStatusView,
    SourceViewSet,
    UploadFeedbackFileView,
)

router = DefaultRouter()
router.register("sources", SourceViewSet, basename="sources")
router.register("feedback-items", FeedbackItemViewSet, basename="feedback-items")

urlpatterns = [
    path("uploads/", UploadFeedbackFileView.as_view(), name="upload-feedback-file"),
    path(
        "uploads/tasks/<str:task_id>/",
        IngestionTaskStatusView.as_view(),
        name="ingestion-task-status",
    ),
    path("", include(router.urls)),
]
