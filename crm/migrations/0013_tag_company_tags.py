import django.db.models.functions.text
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("crm", "0012_lead_deleted_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        db_collation="sv-SE-x-icu",
                        max_length=100,
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
                "constraints": [
                    models.UniqueConstraint(
                        django.db.models.functions.text.Lower("name"),
                        name="unique_tag_name_ci",
                    ),
                ],
            },
        ),
        migrations.AddField(
            model_name="company",
            name="tags",
            field=models.ManyToManyField(
                blank=True,
                related_name="companies",
                to="crm.tag",
            ),
        ),
    ]
