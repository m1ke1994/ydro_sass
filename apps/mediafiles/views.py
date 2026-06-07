from django.db.models import QuerySet
from rest_framework import generics
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from apps.sites.models import Site

from .models import MediaFile
from .serializers import MediaFileSerializer


class ClientMediaAccessMixin:
    permission_classes = [IsAuthenticated]

    def get_client_site(self) -> Site:
        site = Site.objects.filter(owner=self.request.user, is_active=True).order_by("id").first()
        if site is None:
            raise NotFound(detail="Active site for current user was not found.")
        return site

    def get_queryset(self) -> QuerySet[MediaFile]:
        return MediaFile.objects.filter(site=self.get_client_site()).select_related("site")


class ClientMediaListView(ClientMediaAccessMixin, generics.ListAPIView):
    serializer_class = MediaFileSerializer

    def get_queryset(self) -> QuerySet[MediaFile]:
        return super().get_queryset().order_by("-created_at")


class ClientMediaUploadView(ClientMediaAccessMixin, generics.CreateAPIView):
    serializer_class = MediaFileSerializer
    parser_classes = [MultiPartParser, FormParser]

    def _resolve_site(self):
        requested = self.request.data.get("site")
        base_queryset = Site.objects.filter(is_active=True)

        if requested in (None, ""):
            return self.get_client_site()

        site = None
        if str(requested).isdigit():
            site = base_queryset.filter(id=int(requested)).first()
        if site is None:
            site = base_queryset.filter(slug=str(requested)).first()
        if site is None:
            raise NotFound(detail="Site was not found.")

        if not self.request.user.is_superuser and site.owner_id != self.request.user.id:
            raise PermissionDenied(detail="You do not have access to this site.")

        return site

    def perform_create(self, serializer):
        site = self._resolve_site()
        section_key = str(self.request.data.get("section") or "uploads")
        field_key = str(self.request.data.get("field") or "")
        original_name = getattr(self.request.data.get("file"), "name", "")

        existing = MediaFile.objects.filter(
            site=site,
            section_key=section_key,
            field_key=field_key,
            original_name=original_name,
        ).first()
        if existing is not None:
            storage = existing.file.storage
            file_name = existing.file.name
            existing.delete()
            if file_name:
                storage.delete(file_name)

        serializer.save(
            site=site,
            section_key=section_key,
            field_key=field_key,
            original_name=original_name,
        )


class ClientMediaDeleteView(ClientMediaAccessMixin, generics.DestroyAPIView):
    serializer_class = MediaFileSerializer
    lookup_field = "id"

    def perform_destroy(self, instance):
        storage = instance.file.storage
        file_name = instance.file.name

        instance.delete()

        if file_name:
            storage.delete(file_name)


class UploadFileView(ClientMediaUploadView):
    """
    Alias endpoint for uploader integrations.
    POST /api/uploads/
    """
