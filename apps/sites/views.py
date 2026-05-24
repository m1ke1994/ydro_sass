from django.db.models import Count, Q
from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Site, SiteSection
from .serializers import (
    ClientSiteSectionSerializer,
    ClientSiteSectionUpdateSerializer,
    ClientSiteSerializer,
    SiteSectionFormSerializer,
    SiteSectionSerializer,
    SiteSerializer,
)


class PublicSiteDetailView(generics.RetrieveAPIView):
    serializer_class = SiteSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return Site.objects.filter(is_active=True).annotate(
            sections_count=Count("sections", filter=Q(sections__is_active=True))
        )


class PublicSiteSectionsListView(generics.ListAPIView):
    serializer_class = SiteSectionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return SiteSection.objects.filter(
            site__slug=self.kwargs["slug"],
            site__is_active=True,
            is_active=True,
        ).order_by("order", "name")


class ClientSiteMixin:
    permission_classes = [IsAuthenticated]

    def get_client_site(self):
        site = (
            Site.objects.filter(owner=self.request.user, is_active=True)
            .annotate(sections_count=Count("sections", filter=Q(sections__is_active=True)))
            .order_by("id")
            .first()
        )
        if site is None:
            raise NotFound(detail="Active site for current user was not found.")
        return site


class ClientSiteView(ClientSiteMixin, APIView):
    def get(self, request, *args, **kwargs):
        serializer = ClientSiteSerializer(self.get_client_site())
        return Response(serializer.data)


class ClientSiteSectionsListView(ClientSiteMixin, generics.ListAPIView):
    serializer_class = ClientSiteSectionSerializer

    def get_queryset(self):
        return SiteSection.objects.filter(site=self.get_client_site()).order_by("order", "name")


class ClientSiteSectionDetailUpdateView(ClientSiteMixin, generics.RetrieveUpdateAPIView):
    lookup_field = "slug"
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        return SiteSection.objects.filter(site=self.get_client_site())

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return ClientSiteSectionUpdateSerializer
        return ClientSiteSectionSerializer


class ClientSiteSectionFormView(ClientSiteMixin, APIView):
    def get(self, request, slug, *args, **kwargs):
        section = SiteSection.objects.filter(site=self.get_client_site(), slug=slug).first()
        if section is None:
            raise NotFound(detail="Section for current user site was not found.")

        serializer = SiteSectionFormSerializer(section)
        section_data = serializer.data
        return Response(
            {
                "section": section_data,
                "component_key": section_data.get("component_key", ""),
                "schema": section_data.get("schema", {}),
                "content": section_data.get("content", {}),
                "settings": section_data.get("settings", {}),
            }
        )
