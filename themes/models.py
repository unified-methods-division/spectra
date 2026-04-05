import uuid

from django.db import models


class Theme(models.Model):
    class ThemeSource(models.TextChoices):
        MANUAL = "manual", "Manual"
        DISCOVERED = "discovered", "Discovered"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("core.Tenant", on_delete=models.CASCADE, related_name="themes")
    slug = models.TextField()
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    source = models.TextField(choices=ThemeSource.choices, default=ThemeSource.MANUAL)
    parent = models.ForeignKey(
        "themes.Theme",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    first_seen_at = models.DateTimeField(null=True, blank=True)
    item_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "themes"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "slug"], name="uniq_theme_tenant_slug")
        ]
