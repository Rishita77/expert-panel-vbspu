"""Serve only the model-free local interface; never connect to an existing database."""

from django.apps import apps
from django.contrib.staticfiles.management.commands.runserver import Command as RunserverCommand
from django.core.management.base import CommandError


class Command(RunserverCommand):
    help = "Run the local, non-persistent interface preview (no migration/database access)."

    def handle(self, *args, **options):
        if list(apps.get_models()):
            raise CommandError(
                "The preview command is model-free. Use the approved database setup for models."
            )
        options["use_reloader"] = False
        options["insecure_serving"] = True  # Development static files, even with DEBUG=False.
        self.stdout.write("LOCAL PREVIEW: no accounts, database writes or real nominations.")
        super().handle(*args, **options)

    def check_migrations(self):
        # No models are installed. Running the normal migration check would contact
        # an unrelated PostgreSQL instance before the user has approved a schema.
        return
