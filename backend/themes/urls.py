from django.urls import path

from . import views

urlpatterns = [
    path("", views.ThemeListView.as_view(), name="theme-list"),
    path("discover/", views.TriggerDiscoveryView.as_view(), name="theme-discover"),
]
