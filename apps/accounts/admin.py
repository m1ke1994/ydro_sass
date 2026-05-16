from django.contrib import admin

from .models import ClientProfile


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "phone", "created_at")
    search_fields = ("user__username", "user__email", "display_name", "phone")
