from django.core.management.base import BaseCommand
from django.db import transaction

from analysis.models import (
    Correction,
    PromptVersion,
    Recommendation,
    RecommendationEvidence,
    RecommendationOutcome,
)
from ingestion.models import Source
from themes.models import Theme
from trends.models import Alert, TrendSnapshot


class Command(BaseCommand):
    help = "Wipe sources, feedback, themes, analysis/trends rows. Keeps tenants (and auth users)."

    def handle(self, *args, **options):
        with transaction.atomic():
            RecommendationOutcome.objects.all().delete()
            RecommendationEvidence.objects.all().delete()
            Recommendation.objects.all().delete()
            Correction.objects.all().delete()
            PromptVersion.objects.all().delete()
            Alert.objects.all().delete()
            TrendSnapshot.objects.all().delete()
            Theme.objects.all().delete()
            Source.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Done. Tenants unchanged."))
