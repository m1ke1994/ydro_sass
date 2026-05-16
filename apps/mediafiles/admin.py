from django.contrib import admin

from .models import MediaFile


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ("site", "title", "file", "file_type", "mime_type", "size", "created_at")
    list_filter = ("site", "file_type", "mime_type", "created_at")
    search_fields = ("title", "alt", "description", "file", "site__name")
