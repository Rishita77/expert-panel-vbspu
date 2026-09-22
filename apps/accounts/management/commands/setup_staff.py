"""Explicit local operator setup, without passwords in command arguments or logs."""

from getpass import getpass

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import Role, RoleAssignment, StaffUser
from apps.accounts.services import lock_access
from apps.audit.services import record


class Command(BaseCommand):
    help = "Set a staff password locally; --bootstrap creates the first account administrator."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("--bootstrap", action="store_true")
        parser.add_argument("--full-name")

    def handle(self, *args, **options):
        password = getpass("New password (hidden): ")
        if password != getpass("Repeat password (hidden): "):
            raise CommandError("Passwords do not match.")
        try:
            with transaction.atomic():
                lock_access()
                if options["bootstrap"]:
                    if StaffUser.objects.exists():
                        raise CommandError("Bootstrap is only available before any staff exist.")
                    if not options["full_name"]:
                        raise CommandError("--full-name is required for bootstrap.")
                    user = StaffUser(
                        username=options["username"].strip(), full_name=options["full_name"].strip()
                    )
                else:
                    try:
                        user = StaffUser.objects.get(username__iexact=options["username"].strip())
                    except StaffUser.DoesNotExist as exc:
                        raise CommandError(
                            "Create the named account through administration first."
                        ) from exc
                validate_password(password, user)
                user.set_password(password)
                user.is_active = True
                user.full_clean()
                user.save()
                if options["bootstrap"]:
                    RoleAssignment.objects.create(
                        user=user, role=Role.ADMIN, reason="Explicit local bootstrap"
                    )
                record(
                    None,
                    "staff.local_password_setup",
                    user,
                    after={"is_active": True},
                    system_actor="local-operator",
                    reason="Explicit local credential setup; password omitted",
                )
        except ValidationError as exc:
            raise CommandError("; ".join(exc.messages)) from exc
        self.stdout.write("Account enabled. No password has been written to output.")
