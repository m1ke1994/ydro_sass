from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Site, SiteLead, SiteSection
from .serializers import (
    AdminLeadSerializer,
    AdminLeadStatusPatchSerializer,
    AdminMySiteSectionCreateSerializer,
    AdminMySiteSectionPatchSerializer,
    AdminMySiteSectionSerializer,
    AdminMySiteSerializer,
    PublicLeadCreateSerializer,
    PublicSiteSectionSerializer,
    PublicSiteSerializer,
)


def _normalize_domain(value):
    if not value:
        return ""
    normalized = str(value).strip().lower()
    normalized = normalized.replace("http://", "").replace("https://", "")
    return normalized.strip("/")


class PublicSiteDetailView(generics.RetrieveAPIView):
    serializer_class = PublicSiteSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"
    lookup_url_kwarg = "site_slug"

    def get_queryset(self):
        return Site.objects.filter(is_active=True).annotate(
            sections_count=Count("sections", filter=Q(sections__is_active=True))
        )


class PublicSiteSectionsListView(generics.ListAPIView):
    serializer_class = PublicSiteSectionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return SiteSection.objects.filter(
            site__slug=self.kwargs["site_slug"],
            site__is_active=True,
            is_active=True,
        ).order_by("order", "title")


class PublicSiteSectionDetailView(generics.RetrieveAPIView):
    serializer_class = PublicSiteSectionSerializer
    permission_classes = [AllowAny]
    lookup_field = "key"
    lookup_url_kwarg = "section_key"

    def get_queryset(self):
        return SiteSection.objects.filter(
            site__slug=self.kwargs["site_slug"],
            site__is_active=True,
            is_active=True,
        )


class PublicSiteByDomainView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        domain = _normalize_domain(request.query_params.get("domain"))
        if not domain:
            return Response({"detail": "Query param 'domain' is required."}, status=status.HTTP_400_BAD_REQUEST)

        site = (
            Site.objects.filter(is_active=True)
            .annotate(sections_count=Count("sections", filter=Q(sections__is_active=True)))
            .filter(domain__iexact=domain)
            .first()
        )

        if site is None:
            raise NotFound(detail="Active site for this domain was not found.")

        site_data = PublicSiteSerializer(site).data
        sections_data = PublicSiteSectionSerializer(
            SiteSection.objects.filter(site=site, is_active=True).order_by("order", "title"),
            many=True,
        ).data

        return Response({"site": site_data, "sections": sections_data})


class PublicSiteBundleBySlugView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        site = (
            Site.objects.filter(slug=self.kwargs["site_slug"], is_active=True)
            .annotate(sections_count=Count("sections", filter=Q(sections__is_active=True)))
            .first()
        )
        if site is None:
            raise NotFound(detail="Active site was not found.")

        sections = SiteSection.objects.filter(site=site, is_active=True).order_by("order", "title")
        return Response(
            {
                "site": PublicSiteSerializer(site).data,
                "sections": PublicSiteSectionSerializer(sections, many=True).data,
            }
        )


class PublicLeadCreateView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = PublicLeadCreateSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Заполните обязательные поля", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            serializer.save()
        except serializers.ValidationError as exc:
            return Response(
                {"success": False, "message": "Сайт не найден", "errors": exc.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"success": True, "message": "Заявка успешно отправлена"}, status=status.HTTP_201_CREATED)


class PublicSiteLeadCreateBySlugView(PublicLeadCreateView):
    def post(self, request, *args, **kwargs):
        payload = request.data.copy()
        payload["site_slug"] = kwargs["site_slug"]
        serializer = PublicLeadCreateSerializer(data=payload, context={"request": request})
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Заполните обязательные поля", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            serializer.save()
        except serializers.ValidationError as exc:
            return Response(
                {"success": False, "message": "Сайт не найден", "errors": exc.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"success": True, "message": "Заявка успешно отправлена"}, status=status.HTTP_201_CREATED)


class AdminSiteAccessMixin:
    permission_classes = [IsAuthenticated]

    def get_sites_queryset(self):
        base = Site.objects.all()
        if self.request.user.is_superuser:
            return base
        return base.filter(owner=self.request.user)

    def get_site(self):
        site_id = self.kwargs["site_id"]
        site = self.get_sites_queryset().filter(id=site_id).first()
        if site is None:
            raise NotFound(detail="Site was not found.")
        return site

    def get_user_leads_queryset(self):
        queryset = SiteLead.objects.select_related("site")
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(site__owner=self.request.user)


class AdminMySitesListView(AdminSiteAccessMixin, generics.ListAPIView):
    serializer_class = AdminMySiteSerializer

    def get_queryset(self):
        return self.get_sites_queryset().annotate(
            sections_count=Count("sections", filter=Q(sections__is_active=True))
        ).order_by("id")


class AdminMySiteDetailView(AdminSiteAccessMixin, generics.RetrieveAPIView):
    serializer_class = AdminMySiteSerializer
    lookup_field = "id"
    lookup_url_kwarg = "site_id"

    def get_queryset(self):
        return self.get_sites_queryset().annotate(
            sections_count=Count("sections", filter=Q(sections__is_active=True))
        )


class AdminMySiteSectionsListCreateView(AdminSiteAccessMixin, generics.ListCreateAPIView):
    def get_queryset(self):
        return SiteSection.objects.filter(site=self.get_site()).order_by("order", "title")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AdminMySiteSectionCreateSerializer
        return AdminMySiteSectionSerializer

    def perform_create(self, serializer):
        serializer.save(site=self.get_site())


class AdminMySiteSectionDetailView(AdminSiteAccessMixin, generics.RetrieveUpdateDestroyAPIView):
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return SiteSection.objects.filter(site=self.get_site())

    def get_object(self):
        queryset = self.get_queryset()
        return get_object_or_404(queryset, id=self.kwargs["section_id"])

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return AdminMySiteSectionPatchSerializer
        return AdminMySiteSectionSerializer

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminMyLeadsListView(AdminSiteAccessMixin, generics.ListAPIView):
    serializer_class = AdminLeadSerializer

    def get_queryset(self):
        queryset = self.get_user_leads_queryset().order_by("-created_at")
        site_id = self.request.query_params.get("site_id")
        status_value = self.request.query_params.get("status")

        if site_id:
            queryset = queryset.filter(site_id=site_id)
        if status_value:
            queryset = queryset.filter(status=status_value)

        return queryset


class AdminMyLeadDetailView(AdminSiteAccessMixin, generics.RetrieveUpdateAPIView):
    serializer_class = AdminLeadSerializer
    lookup_url_kwarg = "lead_id"
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        return self.get_user_leads_queryset()

    def get_serializer_class(self):
        if self.request.method.lower() == "patch":
            return AdminLeadStatusPatchSerializer
        return AdminLeadSerializer

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = AdminLeadStatusPatchSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AdminLeadSerializer(instance).data, status=status.HTTP_200_OK)
