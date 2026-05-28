# Generated manually for client UUID support.
import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0003_client_send_to_telegram"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="uuid",
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True, verbose_name="Client UUID"),
        ),
    ]
