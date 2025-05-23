# Generated by Django 5.1.6 on 2025-04-08 16:17

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("projects", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectAPIAccess",
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
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("submit-responses", "Submit Responses"),
                            ("explore-responses", "Explore Responses"),
                        ],
                        max_length=18,
                    ),
                ),
                ("expires_at", models.DateTimeField(editable=False)),
                (
                    "lifespan_days",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (30, "30 days"),
                            (60, "60 days"),
                            (90, "90 days"),
                            (180, "180 days"),
                        ]
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        editable=False,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "grantee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="accesses",
                        to="projects.project",
                    ),
                ),
            ],
            options={
                "verbose_name": "project API access",
                "verbose_name_plural": "project API accesses",
                "indexes": [
                    models.Index(
                        fields=["expires_at"],
                        name="api_project_expires_82a9e9_idx",
                    )
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(
                            (
                                "role__in",
                                ["submit-responses", "explore-responses"],
                            )
                        ),
                        name="api_access_role_valid_choice",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("lifespan_days__in", [30, 60, 90, 180])
                        ),
                        name="api_access_role_valid_lifespan",
                    ),
                ],
            },
        ),
    ]
