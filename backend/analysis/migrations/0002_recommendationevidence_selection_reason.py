# Generated manually — field existed on model but was missing from 0001_initial.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analysis", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="recommendationevidence",
            name="selection_reason",
            field=models.TextField(blank=True, null=True),
        ),
    ]
