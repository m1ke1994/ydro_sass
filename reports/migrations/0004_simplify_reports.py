from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0003_rename_reports_rep_client__9f4e1f_idx_reports_rep_client__cef9a3_idx_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="reportsettings",
            old_name="enabled",
            new_name="daily_pdf_enabled",
        ),
        migrations.RemoveField(
            model_name="reportsettings",
            name="daily_time",
        ),
        migrations.RemoveField(
            model_name="reportsettings",
            name="timezone",
        ),
        migrations.RemoveField(
            model_name="reportsettings",
            name="send_email",
        ),
        migrations.RemoveField(
            model_name="reportsettings",
            name="email_to",
        ),
        migrations.RemoveField(
            model_name="reportsettings",
            name="send_telegram",
        ),
        migrations.RemoveField(
            model_name="reportsettings",
            name="telegram_chat_id",
        ),
        migrations.RemoveField(
            model_name="reportsettings",
            name="telegram_username",
        ),
        migrations.RemoveField(
            model_name="reportsettings",
            name="telegram_is_connected",
        ),
        migrations.RemoveField(
            model_name="reportsettings",
            name="last_status",
        ),
        migrations.RemoveField(
            model_name="reportsettings",
            name="user",
        ),
        migrations.DeleteModel(
            name="ReportLog",
        ),
        migrations.DeleteModel(
            name="TelegramLinkToken",
        ),
    ]
