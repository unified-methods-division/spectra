from rest_framework import viewsets

from .models import FeedbackItem, Source
from .serializers import FeedbackItemSerializer, SourceSerializer


class SourceViewSet(viewsets.ModelViewSet):
    queryset = Source.objects.all().order_by("-created_at")
    serializer_class = SourceSerializer


class FeedbackItemViewSet(viewsets.ModelViewSet):
    queryset = FeedbackItem.objects.all().order_by("-received_at")
    serializer_class = FeedbackItemSerializer
