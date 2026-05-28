from django.contrib import admin

from leads.models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "name", "phone", "email", "status", "created_at")
    search_fields = ("name", "phone", "email", "client__name")
    list_filter = ("status", "created_at")
    ordering = ("-created_at",)
