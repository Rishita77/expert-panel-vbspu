import json
import secrets

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import Role, RoleAssignment, StaffUser
from apps.accounts.services import lock_access, save_staff
from apps.audit.services import record
from apps.cases.services import save_record
from apps.institutions.models import Institution, Subject


class Command(BaseCommand):
    help = "Seed an empty local demonstration database with labelled synthetic staff and directory."

    def add_arguments(self, parser):
        parser.add_argument("--synthetic", action="store_true")

    def handle(self, *args, **options):
        if settings.SETTINGS_MODULE != "config.foundation" or not options["synthetic"]:
            raise CommandError("Only for config.foundation with explicit --synthetic.")
        access = {}
        with transaction.atomic():
            lock_access()
            if StaffUser.objects.exists():
                raise CommandError(
                    "Requires an empty staff table; existing accounts are not changed."
                )
            password = secrets.token_urlsafe(18)
            admin = StaffUser.objects.create_user(
                username="demo.admin",
                full_name="परीक्षण खाता प्रशासक",
                password=password,
                is_active=True,
            )
            RoleAssignment.objects.create(
                user=admin, role=Role.ADMIN, reason="Synthetic local demonstration bootstrap"
            )
            record(
                None,
                "staff.created",
                admin,
                after={"username": admin.username, "roles": [Role.ADMIN]},
                system_actor="synthetic-demo-bootstrap",
            )
            access["admin"] = {"username": admin.username, "password": password}
            for name, full_name, roles in [
                ("poc", "परीक्षण कार्यालय अधिकारी", [Role.PROCESSOR, Role.MASTER]),
                ("reviewer", "परीक्षण समीक्षा अधिकारी", [Role.REVIEWER]),
            ]:
                user = save_staff(
                    admin,
                    {"username": f"demo.{name}", "full_name": full_name, "email": ""},
                    roles,
                    "Synthetic local demonstration",
                )
                password = secrets.token_urlsafe(18)
                user.set_password(password)
                user.is_active = True
                user.save()
                record(
                    None,
                    "staff.local_password_setup",
                    user,
                    after={"is_active": True},
                    system_actor="synthetic-demo-bootstrap",
                )
                access[name] = {"username": user.username, "password": password}
                if name == "poc":
                    for college_name in ["परीक्षण महाविद्यालय — जौनपुर", "नमूना महाविद्यालय — आजमगढ़"]:
                        save_record(
                            user,
                            Institution,
                            {
                                "name": college_name,
                                "institution_kind": "college",
                                "management_type": "unknown",
                                "is_active": True,
                            },
                            0,
                        )
                    save_record(user, Subject, {"name": "हिन्दी", "is_active": True}, 0)
        local = settings.BASE_DIR / ".local"
        (local / "demo-access.json").write_text(json.dumps(access), encoding="utf-8")
        lines = [
            "# Local demonstration access",
            "",
            "Synthetic accounts only. Open http://127.0.0.1:8000/office/ .",
            "",
            "Use the POC account for directories and saved Hindi requests.",
            "",
        ]
        for name, item in access.items():
            lines.extend(
                [
                    f"## {name}",
                    "",
                    f"Username: `{item['username']}`",
                    f"Password: `{item['password']}`",
                    "",
                ]
            )
        lines.extend(
            [
                "Keep this local access note private. It is ignored by version control.",
                "These are demonstration credentials, not production accounts.",
            ]
        )
        (local / "demo-access.md").write_text("\n".join(lines), encoding="utf-8")
        self.stdout.write("Synthetic demonstration ready. Access note: .local/demo-access.md")
