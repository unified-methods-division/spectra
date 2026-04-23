from django.urls import path

from . import views

urlpatterns = [
    path(
        "sources/<uuid:source_id>/processing-status/",
        views.ProcessingStatusView.as_view(),
        name="processing-status",
    ),
    path(
        "corrections/",
        views.CorrectionCreateView.as_view(),
        name="correction-create",
    ),
    path(
        "recommendations/",
        views.recommendation_list,
        name="recommendation-list",
    ),
    path(
        "recommendations/<uuid:recommendation_id>/",
        views.recommendation_detail,
        name="recommendation-detail",
    ),
    path(
        "recommendations/<uuid:recommendation_id>/decide/",
        views.recommendation_decide,
        name="recommendation-decide",
    ),
]
