# Generated by Django 5.1.6 on 2025-03-04 17:28

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prompts", "0003_rangedprompt_rangedpromptoption"),
        ("responses", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PromptResponse",
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
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                        verbose_name="ID",
                    ),
                ),
                (
                    "prompt",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="prompts.prompt",
                    ),
                ),
                (
                    "response",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="prompt_responses",
                        to="responses.response",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="BinaryPromptResponse",
            fields=[
                (
                    "promptresponse_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="responses.promptresponse",
                    ),
                ),
                ("value", models.BooleanField()),
            ],
            options={
                "abstract": False,
            },
            bases=("responses.promptresponse",),
        ),
        migrations.CreateModel(
            name="TextPromptResponse",
            fields=[
                (
                    "promptresponse_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="responses.promptresponse",
                    ),
                ),
                ("value", models.TextField()),
            ],
            options={
                "abstract": False,
            },
            bases=("responses.promptresponse",),
        ),
        migrations.CreateModel(
            name="RangedPromptResponse",
            fields=[
                (
                    "promptresponse_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="responses.promptresponse",
                    ),
                ),
                (
                    "value",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="prompts.rangedpromptoption",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("responses.promptresponse",),
        ),
    ]
