from django.db.models import QuerySet
from rest_framework import generics
from rest_framework.exceptions import NotFound
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
            raise NotFound(detail="Активный сайт пользователя не найден.")
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

    def perform_create(self, serializer):
        serializer.save(site=self.get_client_site())


class ClientMediaDeleteView(ClientMediaAccessMixin, generics.DestroyAPIView):
    serializer_class = MediaFileSerializer
    lookup_field = "id"

    def perform_destroy(self, instance):
        storage = instance.file.storage
        file_name = instance.file.name

        instance.delete()

        if file_name:
            storage.delete(file_name)
