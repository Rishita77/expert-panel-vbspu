from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("experts", "0003_split_academic_designation_and_administrative_post")]

    operations = [
        migrations.AddField(
            model_name="appointment",
            name="university",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="university_appointments",
                to="institutions.institution",
                verbose_name="विश्वविद्यालय",
            ),
        ),
    ]
