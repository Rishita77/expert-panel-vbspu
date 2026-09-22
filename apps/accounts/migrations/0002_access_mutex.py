from django.db import migrations


def initialise(apps, schema_editor):
    apps.get_model("accounts", "AccessMutex").objects.using(
        schema_editor.connection.alias
    ).get_or_create(pk=1)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]
    operations = [migrations.RunPython(initialise, migrations.RunPython.noop)]
