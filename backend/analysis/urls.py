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
]
