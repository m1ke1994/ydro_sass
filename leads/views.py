from django.utils.dateparse import parse_date
from django.shortcuts import get_object_or_404
import logging
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from accounts.permissions import IsClientUser
from clients.permissions import HasValidApiKey
from leads.models import Lead
from leads.serializers import LeadSerializer, LeadStatusSerializer, PublicLeadCreateSerializer
from subscriptions.permissions import HasActiveSubscription

logger = logging.getLogger(__name__)


class PublicLeadCreateView(CreateAPIView):
    serializer_class = PublicLeadCreateSerializer
    permission_classes = [HasValidApiKey]
    throttle_scope = "public_lead"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["client"] = self.request.client
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            lead = serializer.save()
        except Exception:
            logger.exception("Failed to create public lead")
            return Response({"detail": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"id": lead.id, "status": lead.status}, status=status.HTTP_201_CREATED)


class LeadViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated, IsClientUser, HasActiveSubscription]
    ordering_fields = ("created_at",)

    def get_queryset(self):
        queryset = Lead.objects.filter(client=self.request.client)
        status_value = self.request.query_params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from and parse_date(date_from):
            queryset = queryset.filter(created_at__date__gte=parse_date(date_from))
        if date_to and parse_date(date_to):
            queryset = queryset.filter(created_at__date__lte=parse_date(date_to))
        return queryset

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        lead = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = LeadStatusSerializer(instance=lead, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(LeadSerializer(lead).data)
