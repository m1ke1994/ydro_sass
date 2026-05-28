# -*- coding: utf-8 -*-
from urllib.parse import urlparse

from rest_framework import serializers

from seo_audit.models import SEOIssue, SEOPage, SiteSEOAudit
from seo_audit.services.messages import (
    get_commercial_business_status,
    get_commercial_explanation,
    get_commercial_recommendations,
    get_commercial_status_label,
    get_conversion_path_label,
    get_issue_title,
)


class SEOAuditStartSerializer(serializers.Serializer):
    domain = serializers.CharField(max_length=255)

    def validate_domain(self, value):
        raw = (value or "").strip()
        if not raw:
            raise serializers.ValidationError("Укажите домен.")
        parsed = urlparse(raw if "://" in raw else f"https://{raw}")
        hostname = (parsed.hostname or "").strip().lower()
        if not hostname:
            raise serializers.ValidationError("Некорректный домен.")
        return hostname


class SEOPageSerializer(serializers.ModelSerializer):
    has_conversion_path = serializers.SerializerMethodField()
    conversion_path_type = serializers.SerializerMethodField()
    conversion_path_type_label = serializers.SerializerMethodField()
    commercial_signals = serializers.SerializerMethodField()
    conversion_signals = serializers.SerializerMethodField()
    contact_signals = serializers.SerializerMethodField()
    cta_signals = serializers.SerializerMethodField()
    messenger_signals = serializers.SerializerMethodField()
    widget_signals = serializers.SerializerMethodField()
    commercial_explanation = serializers.SerializerMethodField()
    commercial_recommendations = serializers.SerializerMethodField()
    commercial_business_status = serializers.SerializerMethodField()
    commercial_business_status_label = serializers.SerializerMethodField()
    commercial_status_label = serializers.SerializerMethodField()

    def _payload(self, obj) -> dict:
        raw = getattr(obj, "commercial_signals_payload", {}) or {}
        return raw if isinstance(raw, dict) else {}

    def _conversion_signals(self, obj) -> dict:
        payload = self._payload(obj)
        source = payload.get("conversion_signals") or {}
        source = source if isinstance(source, dict) else {}
        return {
            "has_form": bool(source.get("has_form", getattr(obj, "has_form", False))),
            "has_cta": bool(source.get("has_cta", getattr(obj, "has_cta", False))),
            "has_direct_contact": bool(source.get("has_direct_contact", getattr(obj, "has_phone_or_contact", False))),
            "has_contact_block": bool(source.get("has_contact_block", False)),
            "has_messenger_contact": bool(source.get("has_messenger_contact", getattr(obj, "has_messenger", False))),
            "has_widget": bool(source.get("has_widget", False)),
            "has_multi_channel_contact": bool(source.get("has_multi_channel_contact", False)),
            "has_offer_like_heading": bool(source.get("has_offer_like_heading", getattr(obj, "has_offer_like_heading", False))),
            "has_benefits_block": bool(source.get("has_benefits_block", getattr(obj, "has_benefits_block", False))),
            "has_faq": bool(source.get("has_faq", getattr(obj, "has_faq", False))),
        }

    def _resolved_conversion_path_type(self, obj) -> str:
        payload = self._payload(obj)
        raw = str(getattr(obj, "conversion_path_type", "") or payload.get("conversion_path_type") or "").strip().lower()
        if raw in {
            SEOPage.ConversionPathType.NONE,
            SEOPage.ConversionPathType.FORM,
            SEOPage.ConversionPathType.CONTACTS,
            SEOPage.ConversionPathType.MESSENGER,
            SEOPage.ConversionPathType.WIDGET,
            SEOPage.ConversionPathType.MIXED,
        }:
            return raw

        signals = self._conversion_signals(obj)
        active = [
            bool(signals.get("has_form")),
            bool(signals.get("has_direct_contact") or signals.get("has_contact_block")),
            bool(signals.get("has_messenger_contact")),
            bool(signals.get("has_widget")),
        ]
        enabled = sum(1 for item in active if item)
        if enabled <= 0:
            return SEOPage.ConversionPathType.NONE
        if enabled > 1:
            return SEOPage.ConversionPathType.MIXED
        if bool(signals.get("has_form")):
            return SEOPage.ConversionPathType.FORM
        if bool(signals.get("has_messenger_contact")):
            return SEOPage.ConversionPathType.MESSENGER
        if bool(signals.get("has_widget")):
            return SEOPage.ConversionPathType.WIDGET
        return SEOPage.ConversionPathType.CONTACTS

    def get_has_conversion_path(self, obj):
        payload = self._payload(obj)
        if bool(getattr(obj, "has_conversion_path", False)):
            return True
        if payload.get("has_conversion_path") is True:
            return True
        signals = self._conversion_signals(obj)
        return bool(
            signals.get("has_form")
            or signals.get("has_direct_contact")
            or signals.get("has_contact_block")
            or signals.get("has_messenger_contact")
            or signals.get("has_widget")
        )

    def get_conversion_path_type(self, obj):
        return self._resolved_conversion_path_type(obj)

    def get_conversion_path_type_label(self, obj):
        return get_conversion_path_label(self.get_conversion_path_type(obj))

    def get_conversion_signals(self, obj):
        return self._conversion_signals(obj)

    def get_contact_signals(self, obj):
        payload = self._payload(obj)
        source = payload.get("contact_signals") or {}
        source = source if isinstance(source, dict) else {}
        return {
            "has_tel_link": bool(source.get("has_tel_link")),
            "has_mailto_link": bool(source.get("has_mailto_link")),
            "has_phone_in_text": bool(source.get("has_phone_in_text")),
            "has_email_in_text": bool(source.get("has_email_in_text")),
            "contact_blocks_count": int(source.get("contact_blocks_count") or 0),
        }

    def get_cta_signals(self, obj):
        payload = self._payload(obj)
        source = payload.get("cta_signals") or {}
        source = source if isinstance(source, dict) else {}
        return {
            "count": int(source.get("count") or 0),
            "matched_texts": list(source.get("matched_texts") or []),
            "matched_attrs": list(source.get("matched_attrs") or []),
        }

    def get_messenger_signals(self, obj):
        payload = self._payload(obj)
        source = payload.get("messenger_signals") or {}
        source = source if isinstance(source, dict) else {}
        return {
            "links_count": int(source.get("links_count") or 0),
            "links_in_contact_context": int(source.get("links_in_contact_context") or 0),
            "platforms": list(source.get("platforms") or []),
            "has_actionable_link": bool(source.get("has_actionable_link")),
        }

    def get_widget_signals(self, obj):
        payload = self._payload(obj)
        source = payload.get("widget_signals") or {}
        source = source if isinstance(source, dict) else {}
        return {
            "has_widget": bool(source.get("has_widget")),
            "matched_hints": list(source.get("matched_hints") or []),
        }

    def get_commercial_signals(self, obj):
        signals = self._conversion_signals(obj)
        return {
            "has_form": bool(signals.get("has_form")),
            "has_cta": bool(signals.get("has_cta")),
            "has_phone_or_contact": bool(
                signals.get("has_direct_contact")
                or signals.get("has_contact_block")
                or signals.get("has_messenger_contact")
                or signals.get("has_widget")
            ),
            "has_messenger": bool(signals.get("has_messenger_contact")),
            "has_offer_like_heading": bool(signals.get("has_offer_like_heading")),
            "has_benefits_block": bool(signals.get("has_benefits_block")),
            "has_faq": bool(signals.get("has_faq")),
            "has_direct_contact": bool(signals.get("has_direct_contact")),
            "has_contact_block": bool(signals.get("has_contact_block")),
            "has_messenger_contact": bool(signals.get("has_messenger_contact")),
            "has_widget": bool(signals.get("has_widget")),
            "has_multi_channel_contact": bool(signals.get("has_multi_channel_contact")),
            "has_conversion_path": self.get_has_conversion_path(obj),
            "conversion_path_type": self.get_conversion_path_type(obj),
        }

    def get_commercial_recommendations(self, obj):
        signals = self.get_commercial_signals(obj)
        return get_commercial_recommendations(
            signals,
            has_conversion_path=self.get_has_conversion_path(obj),
            conversion_path_type=self.get_conversion_path_type(obj),
            score=int(getattr(obj, "commercial_readiness_score", 0) or 0),
        )

    def get_commercial_explanation(self, obj):
        signals = self.get_commercial_signals(obj)
        return get_commercial_explanation(
            signals=signals,
            has_conversion_path=self.get_has_conversion_path(obj),
            conversion_path_type=self.get_conversion_path_type(obj),
            status_key=getattr(obj, "commercial_status", "warning"),
            score=int(getattr(obj, "commercial_readiness_score", 0) or 0),
        )

    def get_commercial_business_status(self, obj):
        signals = self.get_commercial_signals(obj)
        return get_commercial_business_status(
            status_key=getattr(obj, "commercial_status", "warning"),
            signals=signals,
            has_conversion_path=self.get_has_conversion_path(obj),
            conversion_path_type=self.get_conversion_path_type(obj),
            score=int(getattr(obj, "commercial_readiness_score", 0) or 0),
        )

    def get_commercial_business_status_label(self, obj):
        return get_commercial_status_label(
            getattr(obj, "commercial_status", "warning"),
            signals=self.get_commercial_signals(obj),
            has_conversion_path=self.get_has_conversion_path(obj),
            conversion_path_type=self.get_conversion_path_type(obj),
            score=int(getattr(obj, "commercial_readiness_score", 0) or 0),
        )

    def get_commercial_status_label(self, obj):
        return get_commercial_status_label(
            getattr(obj, "commercial_status", "warning"),
            signals=self.get_commercial_signals(obj),
            has_conversion_path=self.get_has_conversion_path(obj),
            conversion_path_type=self.get_conversion_path_type(obj),
            score=int(getattr(obj, "commercial_readiness_score", 0) or 0),
        )

    class Meta:
        model = SEOPage
        fields = (
            "id",
            "url",
            "status_code",
            "ttfb_ms",
            "html_size_bytes",
            "js_files_count",
            "css_files_count",
            "images_count",
            "total_js_bytes",
            "total_css_bytes",
            "total_image_bytes",
            "performance_score",
            "speed_status",
            "title",
            "title_length",
            "description",
            "description_length",
            "h1",
            "h1_count",
            "word_count",
            "meta_robots",
            "canonical_url",
            "indexability_status",
            "in_sitemap",
            "blocked_by_robots",
            "has_form",
            "has_cta",
            "has_phone_or_contact",
            "has_messenger",
            "has_offer_like_heading",
            "has_benefits_block",
            "has_faq",
            "has_conversion_path",
            "conversion_path_type",
            "conversion_path_type_label",
            "commercial_readiness_score",
            "commercial_status",
            "commercial_status_label",
            "commercial_business_status",
            "commercial_business_status_label",
            "commercial_signals",
            "conversion_signals",
            "contact_signals",
            "cta_signals",
            "messenger_signals",
            "widget_signals",
            "commercial_explanation",
            "commercial_recommendations",
        )


class SEOIssueSerializer(serializers.ModelSerializer):
    page_id = serializers.IntegerField(read_only=True)
    page_url = serializers.CharField(source="page.url", read_only=True)
    issue_title = serializers.SerializerMethodField()

    def get_issue_title(self, obj):
        return get_issue_title(obj.issue_type)

    class Meta:
        model = SEOIssue
        fields = ("id", "page_id", "page_url", "issue_type", "issue_title", "severity", "recommendation")


class SiteSEOAuditSerializer(serializers.ModelSerializer):
    score = serializers.IntegerField(source="seo_score", read_only=True)

    class Meta:
        model = SiteSEOAudit
        fields = (
            "id",
            "domain",
            "status",
            "score",
            "seo_score",
            "pages_count",
            "used_sitemap",
            "sitemap_urls_count",
            "pages_with_speed_issues",
            "pages_with_indexing_issues",
            "has_robots_txt",
            "has_sitemap_xml",
            "avg_ttfb_ms",
            "avg_performance_score",
            "created_at",
            "finished_at",
        )
