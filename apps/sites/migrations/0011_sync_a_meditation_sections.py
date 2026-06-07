from copy import deepcopy

from django.db import migrations


def sync_a_meditation_sections(apps, schema_editor):
    from apps.sites.a_meditation import (
        A_MEDITATION_SECTION_SEEDS,
        merge_content_defaults,
    )

    Site = apps.get_model("sites", "Site")
    SiteSection = apps.get_model("sites", "SiteSection")
    SectionSchema = apps.get_model("sites", "SectionSchema")

    site = Site.objects.filter(slug="a-meditation").first()
    if site is None:
        return
    if site.domain in {"", "localhost"}:
        site.domain = "localhost:5173"
        site.save(update_fields=["domain", "updated_at"])

    for seed in A_MEDITATION_SECTION_SEEDS:
        schema = deepcopy(seed["schema"])
        defaults = deepcopy(seed["content"])

        SectionSchema.objects.update_or_create(
            section_key=seed["key"],
            defaults={
                "title": seed["title"],
                "schema": schema,
                "description": f"Поля раздела «{seed['title']}»",
            },
        )

        section, created = SiteSection.objects.get_or_create(
            site=site,
            key=seed["key"],
            defaults={
                "title": seed["title"],
                "section_type": seed["key"],
                "order": seed["order"],
                "is_active": True,
                "schema": schema,
                "content": defaults,
                "component_key": f"{seed['key']}-section",
                "settings": {},
                "seo": {},
            },
        )
        if created:
            continue

        section.title = seed["title"]
        section.section_type = seed["key"]
        section.order = seed["order"]
        section.is_active = True
        section.schema = schema
        section.content = merge_content_defaults(defaults, section.content)
        section.component_key = section.component_key or f"{seed['key']}-section"
        section.save(
            update_fields=[
                "title",
                "section_type",
                "order",
                "is_active",
                "schema",
                "content",
                "component_key",
                "updated_at",
            ]
        )

    SiteSection.objects.filter(site=site, key="about").update(is_active=False)


class Migration(migrations.Migration):
    dependencies = [
        ("sites", "0010_alter_site_options_site_send_to_telegram_and_more"),
    ]

    operations = [
        migrations.RunPython(sync_a_meditation_sections, migrations.RunPython.noop),
    ]
