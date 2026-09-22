from django.conf import settings
from django.contrib.staticfiles.management.commands.runserver import Command as RunserverCommand
from django.core.management.base import CommandError


class Command(RunserverCommand):
    help = "Run the approved local persistent demonstration, bound to loopback only."

    def handle(self, *args, **options):
        if settings.SETTINGS_MODULE != "config.foundation":
            raise CommandError("Use --settings=config.foundation")
        address = options.get("addrport") or "127.0.0.1:8000"
        if not address.startswith(("127.0.0.1:", "localhost:")):
            raise CommandError("Local demonstration must bind to loopback.")
        options["addrport"] = address
        options["use_reloader"] = False
        options["insecure_serving"] = True
        self.stdout.write("LOCAL FOUNDATION: saved drafts; no operational nominations.")
        super().handle(*args, **options)
