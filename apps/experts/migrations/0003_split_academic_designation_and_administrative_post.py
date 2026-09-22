# Generated manually to preserve existing appointment history.

from django.db import migrations, models


def separate_existing_appointment_facts(apps, schema_editor):
    Appointment = apps.get_model("experts", "Appointment")
    # Earlier records used designation for both academic and administrative roles.
    # Academic information is preserved by the renamed academic_designation field;
    # non-Principal values therefore become "no administrative post".
    Appointment.objects.filter(
        administrative_post__in=["professor", "assistant", "other"]
    ).update(administrative_post="")


class Migration(migrations.Migration):
    dependencies = [("experts", "0002_sequence_and_history_guards")]

    operations = [
        migrations.RemoveConstraint(
            model_name="appointment", name="appointment_designation_valid"
        ),
        migrations.RemoveConstraint(model_name="appointment", name="appointment_rank_valid"),
        migrations.RenameField(
            model_name="appointment", old_name="designation", new_name="administrative_post"
        ),
        migrations.RenameField(
            model_name="appointment", old_name="academic_rank", new_name="academic_designation"
        ),
        migrations.AddField(
            model_name="appointment",
            name="administrative_post_title",
            field=models.CharField(blank=True, max_length=200, verbose_name="अन्य प्रशासनिक पद का नाम"),
        ),
        migrations.AddField(
            model_name="appointment",
            name="post_end_date",
            field=models.DateField(blank=True, null=True, verbose_name="प्रशासनिक पद समाप्ति (यदि ज्ञात हो)"),
        ),
        migrations.RunPython(separate_existing_appointment_facts, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="appointment",
            name="administrative_post",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "कोई प्रशासनिक पद नहीं"),
                    ("principal", "प्राचार्य"),
                    ("hod", "विभागाध्यक्ष"),
                    ("other", "अन्य प्रशासनिक पद"),
                ],
                max_length=20,
                verbose_name="धारित प्रशासनिक पद",
            ),
        ),
        migrations.AlterField(
            model_name="appointment",
            name="academic_designation",
            field=models.CharField(
                choices=[
                    ("professor", "प्रोफेसर"),
                    ("assistant", "सहायक प्रोफेसर"),
                    ("other", "अन्य"),
                    ("unknown", "सत्यापन शेष"),
                ],
                default="unknown",
                max_length=20,
                verbose_name="शैक्षणिक पदनाम",
            ),
        ),
        migrations.AddConstraint(
            model_name="appointment",
            constraint=models.CheckConstraint(
                condition=models.Q(administrative_post__in=["", "principal", "hod", "other"]),
                name="appointment_administrative_post_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="appointment",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    academic_designation__in=["professor", "assistant", "other", "unknown"]
                ),
                name="appointment_academic_designation_valid",
            ),
        ),
    ]
