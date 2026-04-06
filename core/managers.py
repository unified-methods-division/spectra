from django.db import models

from .middleware import get_current_tenant


class TenantManager(models.Manager):
    """Auto-filters querysets by the current tenant from contextvar."""

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_current_tenant()
        if tenant is not None:
            qs = qs.filter(tenant=tenant)
        return qs
