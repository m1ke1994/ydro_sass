# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("seo_audit", "0004_rename_seo_audit_s_audit_i_4e9b6c_idx_seo_audit_s_audit_i_15cee6_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="seopage",
            name="blocked_by_robots",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="seopage",
            name="canonical_url",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="seopage",
            name="css_files_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="seopage",
            name="html_size_bytes",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="seopage",
            name="images_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="seopage",
            name="in_sitemap",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="seopage",
            name="indexability_status",
            field=models.CharField(
                choices=[
                    ("unknown", "Не определено"),
                    ("indexable", "Индексируется"),
                    ("noindex", "Noindex"),
                    ("blocked", "Заблокировано robots.txt"),
                    ("conflict", "Конфликт индексации"),
                ],
                default="unknown",
                max_length=24,
            ),
        ),
        migrations.AddField(
            model_name="seopage",
            name="js_files_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="seopage",
            name="meta_robots",
            field=models.CharField(blank=True, default="", max_length=512),
        ),
        migrations.AddField(
            model_name="seopage",
            name="performance_score",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="seopage",
            name="speed_status",
            field=models.CharField(
                choices=[
                    ("unknown", "Не определено"),
                    ("good", "Хорошо"),
                    ("warning", "Есть замечания"),
                    ("critical", "Критично"),
                ],
                default="unknown",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="seopage",
            name="total_css_bytes",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="seopage",
            name="total_image_bytes",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="seopage",
            name="total_js_bytes",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="seopage",
            name="ttfb_ms",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="siteseoaudit",
            name="avg_performance_score",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="siteseoaudit",
            name="avg_ttfb_ms",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="siteseoaudit",
            name="has_robots_txt",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="siteseoaudit",
            name="has_sitemap_xml",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="siteseoaudit",
            name="pages_with_indexing_issues",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="siteseoaudit",
            name="pages_with_speed_issues",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="seoissue",
            name="issue_type",
            field=models.CharField(
                choices=[
                    ("missing_title", "missing_title"),
                    ("bad_title_length", "bad_title_length"),
                    ("title_too_short", "title_too_short"),
                    ("title_too_long", "title_too_long"),
                    ("missing_description", "missing_description"),
                    ("description_too_short", "description_too_short"),
                    ("description_too_long", "description_too_long"),
                    ("duplicate_title", "duplicate_title"),
                    ("missing_h1", "missing_h1"),
                    ("multiple_h1", "multiple_h1"),
                    ("long_h1", "long_h1"),
                    ("heading_hierarchy_gap", "heading_hierarchy_gap"),
                    ("low_word_count", "low_word_count"),
                    ("image_missing_alt", "image_missing_alt"),
                    ("image_empty_alt", "image_empty_alt"),
                    ("bad_status", "bad_status"),
                    ("network_error", "network_error"),
                    ("redirect", "redirect"),
                    ("slow_response", "slow_response"),
                    ("large_page_size", "large_page_size"),
                    ("slow_ttfb", "slow_ttfb"),
                    ("large_html_size", "large_html_size"),
                    ("too_many_js", "too_many_js"),
                    ("too_many_css", "too_many_css"),
                    ("too_many_images", "too_many_images"),
                    ("heavy_js_payload", "heavy_js_payload"),
                    ("heavy_css_payload", "heavy_css_payload"),
                    ("heavy_images_payload", "heavy_images_payload"),
                    ("heavy_page_payload", "heavy_page_payload"),
                    ("missing_canonical", "missing_canonical"),
                    ("invalid_canonical", "invalid_canonical"),
                    ("canonical_conflict", "canonical_conflict"),
                    ("page_noindex", "page_noindex"),
                    ("page_nofollow", "page_nofollow"),
                    ("blocked_by_robots", "blocked_by_robots"),
                    ("sitemap_page_missing", "sitemap_page_missing"),
                    ("missing_meta_robots", "missing_meta_robots"),
                    ("missing_viewport", "missing_viewport"),
                    ("missing_charset", "missing_charset"),
                    ("missing_robots_txt", "missing_robots_txt"),
                    ("robots_disallow_all", "robots_disallow_all"),
                    ("robots_missing_sitemap", "robots_missing_sitemap"),
                    ("missing_sitemap", "missing_sitemap"),
                    ("bad_sitemap_status", "bad_sitemap_status"),
                    ("sitemap_mismatch", "sitemap_mismatch"),
                ],
                max_length=64,
            ),
        ),
    ]
