from celery import shared_task
from django.utils import timezone

from core.models import Tenant

from .engine import compute_daily_accuracy


@shared_task(name="trends.compute_daily_snapshots")
def compute_daily_snapshots():
    """Compute daily accuracy snapshots for all tenants."""
    today = timezone.localdate()
    for tenant in Tenant.objects.all():
        compute_daily_accuracy(str(tenant.id), today)
