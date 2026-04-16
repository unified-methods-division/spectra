from celery import shared_task

from core.models import Tenant
from themes.discovery import discover_themes


@shared_task(name="themes.discover_themes_for_source")
def discover_themes_for_source(source_id: str) -> dict:
    from ingestion.models import Source

    tid = Source.objects.only("tenant_id").get(pk=source_id).tenant_id
    return discover_themes(str(tid))


@shared_task(name="themes.discover_themes_for_tenant")
def discover_themes_for_tenant(tenant_id: str) -> dict:
    return discover_themes(tenant_id)


@shared_task(name="themes.discover_themes_for_all_tenants")
def discover_themes_for_all_tenants() -> None:
    for tid in Tenant.objects.values_list("id", flat=True):
        discover_themes_for_tenant.delay(str(tid))
