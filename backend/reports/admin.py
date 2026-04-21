from django.contrib import admin

from .models import Report, ReportSection


class ReportSectionInline(admin.TabularInline):
    model = ReportSection
    extra = 0
    readonly_fields = ["id", "section_type", "order", "created_at"]
    fields = ["section_type", "order", "raw_content", "polished_content"]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "tenant",
        "report_type",
        "period_start",
        "period_end",
        "status",
        "created_at",
    ]
    list_filter = ["status", "report_type", "tenant"]
    search_fields = ["id", "tenant__name"]
    readonly_fields = ["id", "task_id", "generated_at", "created_at"]
    inlines = [ReportSectionInline]


@admin.register(ReportSection)
class ReportSectionAdmin(admin.ModelAdmin):
    list_display = ["id", "report", "section_type", "order", "created_at"]
    list_filter = ["section_type"]
    readonly_fields = ["id", "created_at"]
