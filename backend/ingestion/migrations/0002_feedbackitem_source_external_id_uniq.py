from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ingestion", "0001_initial"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="feedbackitem",
            constraint=models.UniqueConstraint(
                fields=("source", "external_id"),
                name="uq_feedback_source_extid",
                condition=models.Q(("external_id__isnull", False)),
            ),
        ),
    ]
