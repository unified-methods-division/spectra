import contextvars

from django.http import JsonResponse

from .models import Tenant

_current_tenant: contextvars.ContextVar[Tenant | None] = contextvars.ContextVar(
    "current_tenant", default=None
)


def get_current_tenant() -> Tenant | None:
    return _current_tenant.get()


# Paths that don't require a tenant header (admin, health checks, etc.)
TENANT_EXEMPT_PREFIXES = ("/admin/", "/health/")


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if any(request.path.startswith(p) for p in TENANT_EXEMPT_PREFIXES):
            return self.get_response(request)

        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            return JsonResponse(
                {"detail": "X-Tenant-ID header is required."},
                status=403,
            )

        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except (Tenant.DoesNotExist, ValueError):
            return JsonResponse(
                {"detail": "Invalid tenant."},
                status=403,
            )

        _current_tenant.set(tenant)
        request.tenant = tenant

        try:
            return self.get_response(request)
        finally:
            _current_tenant.set(None)
