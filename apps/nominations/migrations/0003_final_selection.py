import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("nominations", "0002_history_guards"),
        ("experts", "0002_sequence_and_history_guards"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="FinalSelection",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True, default=uuid.uuid4, editable=False, serialize=False
                    ),
                ),
                (
                    "state",
                    models.CharField(
                        max_length=20,
                        default="draft",
                        choices=[
                            ("draft", "प्रारूप"),
                            ("submitted", "समीक्षा हेतु प्रस्तुत"),
                            ("returned", "वापस किया गया"),
                            ("locked", "अंतिम रूप से लॉक"),
                        ],
                    ),
                ),
                ("revision", models.PositiveIntegerField(default=1)),
                ("management_reference", models.CharField(max_length=500, blank=True)),
                ("management_date", models.DateField(null=True, blank=True)),
                ("vc_reference", models.CharField(max_length=500, blank=True)),
                ("vc_date", models.DateField(null=True, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("submitted_at", models.DateTimeField(null=True, blank=True)),
                ("locked_at", models.DateTimeField(null=True, blank=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "locked_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        null=True,
                        blank=True,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "request",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="cases.requestdraft"
                    ),
                ),
                (
                    "source_run",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT, to="nominations.allocationrun"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="FinalMember",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True, default=uuid.uuid4, editable=False, serialize=False
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("vc", "कुलपति नामित"),
                            ("principal", "प्राचार्य"),
                            ("professor", "प्रोफेसर"),
                            ("scst", "अतिरिक्त SC/ST"),
                            ("obc", "अतिरिक्त OBC"),
                        ],
                    ),
                ),
                ("position", models.PositiveSmallIntegerField(default=1)),
                ("selected", models.BooleanField(default=False)),
                ("snapshot", models.JSONField()),
                (
                    "expert",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="experts.expert"
                    ),
                ),
                (
                    "selection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="members",
                        to="nominations.finalselection",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="FinalReviewEvent",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True, default=uuid.uuid4, editable=False, serialize=False
                    ),
                ),
                ("revision", models.PositiveIntegerField()),
                (
                    "action",
                    models.CharField(
                        max_length=20,
                        choices=[("submitted", "प्रस्तुत"), ("returned", "वापस"), ("locked", "लॉक")],
                    ),
                ),
                ("reason", models.CharField(max_length=1000, blank=True)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    "selection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="review_events",
                        to="nominations.finalselection",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UtilisationEntry",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True, default=uuid.uuid4, editable=False, serialize=False
                    ),
                ),
                ("role", models.CharField(max_length=20)),
                ("appointment_type", models.CharField(max_length=30)),
                ("nomination_year", models.CharField(max_length=9)),
                ("locked_at", models.DateTimeField()),
                ("snapshot", models.JSONField()),
                (
                    "expert",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="experts.expert"
                    ),
                ),
                (
                    "member",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="utilisation",
                        to="nominations.finalmember",
                    ),
                ),
                (
                    "selection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="nominations.finalselection"
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="finalselection",
            constraint=models.CheckConstraint(
                condition=models.Q(state__in=["draft", "submitted", "returned", "locked"]),
                name="final_selection_state_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="finalmember",
            constraint=models.UniqueConstraint(
                fields=("selection", "expert"), name="final_member_unique_person"
            ),
        ),
        migrations.AddConstraint(
            model_name="finalmember",
            constraint=models.UniqueConstraint(
                fields=("selection", "role", "position"), name="final_member_unique_seat"
            ),
        ),
    ]
