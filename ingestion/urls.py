from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FeedbackItemViewSet, SourceViewSet

router = DefaultRouter()
router.register("sources", SourceViewSet, basename="sources")
router.register("feedback-items", FeedbackItemViewSet, basename="feedback-items")

urlpatterns = [
    path("", include(router.urls)),
]
