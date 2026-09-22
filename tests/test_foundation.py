from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

import pytest
from django.conf import settings

if settings.SETTINGS_MODULE != "config.foundation":
    pytest.skip("Run with --ds=config.foundation against PostgreSQL.", allow_module_level=True)

from django.core.exceptions import PermissionDenied, ValidationError  # noqa: E402
from django.db import IntegrityError, close_old_connections, connection, transaction  # noqa: E402
from django.db.models.deletion import ProtectedError  # noqa: E402
from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402

from apps.accounts.models import AccessMutex, Role, RoleAssignment, StaffUser  # noqa: E402
from apps.accounts.services import save_staff  # noqa: E402
from apps.audit.models import AuditEvent  # noqa: E402
from apps.cases.forms import InstitutionForm  # noqa: E402
from apps.cases.models import RequestDraft  # noqa: E402
from apps.cases.services import EditConflict, save_record  # noqa: E402
from apps.institutions.models import Institution  # noqa: E402

pytestmark = pytest.mark.django_db


def test_institution_change_reason_only_appears_for_existing_records():
    new_form = InstitutionForm()
    assert "reason" not in new_form.fields
    assert new_form.fields["is_affiliated_to_vbspu"].required
    existing = Institution(name="Existing", institution_kind="college")
    existing._state.adding = False
    form = InstitutionForm(instance=existing)
    assert form.fields["reason"].required
    assert not form.fields["is_affiliated_to_vbspu"].required


@pytest.fixture
def people():
    AccessMutex.objects.get_or_create(pk=1)
    result = {}
    for role in Role.values:
        user = StaffUser.objects.create_user(
            username=role,
            full_name=f"परीक्षण {role}",
            password="Synthetic-Only-7!Testing",
            is_active=True,
        )
        RoleAssignment.objects.create(user=user, role=role, reason="Test fixture")
        result[role] = user
    return result


@pytest.fixture
def college(people):
    return save_record(
        people["master"],
        Institution,
        {
            "name": "परीक्षण महाविद्यालय",
            "institution_kind": "college",
            "management_type": "aided",
            "is_active": True,
        },
        0,
    )


def draft(people, college):
    return save_record(
        people["processor"],
        RequestDraft,
        {
            "institution": college,
            "appointment_type": "subject_expert",
            "remarks": "संयुक्ताक्षर क्ष त्र ज्ञ — हिन्दी",
        },
        0,
    )


def test_database_is_postgresql_17():
    assert connection.vendor == "postgresql"
    assert 170000 <= connection.pg_version < 180000


@pytest.mark.parametrize("kind", ["requests", "institutions", "subjects", "staff"])
def test_anonymous_redirect(client, kind):
    assert client.get(reverse("office_list", args=[kind])).status_code == 302


@pytest.mark.parametrize(
    "role,kind,read,write",
    [
        ("admin", "requests", 403, 403),
        ("admin", "institutions", 200, 403),
        ("master", "institutions", 200, 200),
        ("master", "requests", 403, 403),
        ("processor", "requests", 200, 200),
        ("processor", "staff", 403, 403),
        ("reviewer", "requests", 200, 403),
        ("reviewer", "subjects", 200, 403),
    ],
)
def test_access_matrix(client, people, role, kind, read, write):
    client.force_login(people[role])
    assert client.get(reverse("office_list", args=[kind])).status_code == read
    assert client.get(reverse("office_new", args=[kind])).status_code == write
    if write == 403:
        assert client.post(reverse("office_new", args=[kind]), {}).status_code == 403


def test_hindi_persistence_and_history(client, people, college):
    client.force_login(people["processor"])
    response = client.post(
        reverse("office_new", args=["requests"]),
        {
            "institution": college.pk,
            "appointment_type": "subject_expert",
            "revision": 0,
            "remarks": "क्षेत्रीय हिन्दी / परीक्षण",
            "candidate_count": 0,
        },
    )
    assert response.status_code == 302
    obj = RequestDraft.objects.get()
    assert obj.candidate_count == 0
    assert obj.remarks == "क्षेत्रीय हिन्दी / परीक्षण"
    assert "क्षेत्रीय हिन्दी" in client.get(response.url).content.decode()
    response = client.post(
        reverse("office_edit", args=["requests", obj.pk]),
        {
            "institution": college.pk,
            "appointment_type": "subject_expert",
            "revision": 1,
            "remarks": "संशोधित हिन्दी",
            "reason": "महाविद्यालय का सुधार",
        },
    )
    assert response.status_code == 302
    obj.refresh_from_db()
    assert obj.revision == 2
    events = AuditEvent.objects.filter(target_id=obj.pk)
    assert events.count() == 2
    assert events.first().before["remarks"] == "क्षेत्रीय हिन्दी / परीक्षण"
    assert events.first().after["remarks"] == "संशोधित हिन्दी"
    assert events.first().actor == people["processor"]


def test_minimum_draft_and_no_submission(client, people, college):
    client.force_login(people["processor"])
    response = client.post(reverse("office_new", args=["requests"]), {"revision": 0})
    assert response.status_code == 200
    assert not RequestDraft.objects.exists()
    obj = draft(people, college)
    assert obj.selection_date is None
    assert client.post(f"/office/requests/{obj.pk}/lock/").status_code == 404
    assert client.post(f"/office/requests/{obj.pk}/delete/").status_code == 404


def test_stale_edit_preserves_text_and_audit(client, people, college):
    obj = draft(people, college)
    save_record(
        people["processor"],
        RequestDraft,
        {"institution": college, "appointment_type": "subject_expert", "remarks": "पहला बदलाव"},
        1,
        obj.pk,
    )
    client.force_login(people["processor"])
    response = client.post(
        reverse("office_edit", args=["requests", obj.pk]),
        {
            "institution": college.pk,
            "appointment_type": "subject_expert",
            "revision": 1,
            "remarks": "दूसरे अधिकारी का पाठ",
            "reason": "सुधार",
        },
    )
    assert response.status_code == 409
    assert "दूसरे अधिकारी का पाठ" in response.content.decode()
    obj.refresh_from_db()
    assert obj.remarks == "पहला बदलाव"
    assert AuditEvent.objects.filter(target_id=obj.pk).count() == 2


def test_audit_failure_rolls_back(people, college):
    with patch("apps.cases.services.record", side_effect=RuntimeError("audit failure")):
        with pytest.raises(RuntimeError):
            draft(people, college)
    assert not RequestDraft.objects.exists()


def test_inactive_college_rejected_but_existing_preserved(people, college):
    obj = draft(people, college)
    college.is_active = False
    college.save()
    with pytest.raises(ValidationError):
        draft(people, college)
    saved = save_record(
        people["processor"],
        RequestDraft,
        {"institution": college, "appointment_type": "subject_expert", "remarks": "इतिहास सुरक्षित"},
        1,
        obj.pk,
    )
    assert saved.institution_id == college.pk


def test_non_college_institution_rejected(people, college):
    university = save_record(
        people["master"],
        Institution,
        {
            "name": "परीक्षण विश्वविद्यालय",
            "institution_kind": "university",
            "management_type": "government",
        },
        0,
    )
    with pytest.raises(ValidationError):
        draft(people, university)


def test_disable_and_role_revocation_stop_existing_session(client, people, college):
    user = people["processor"]
    client.force_login(user)
    assert client.get("/office/requests/").status_code == 200
    user.is_active = False
    user.save()
    assert client.get("/office/requests/").status_code == 302
    user.is_active = True
    user.save()
    client.force_login(user)
    from django.utils import timezone

    RoleAssignment.objects.filter(user=user).update(revoked_at=timezone.now())
    assert client.get("/office/requests/").status_code == 403


def test_service_rechecks_disabled_actor(people, college):
    StaffUser.objects.filter(pk=people["processor"].pk).update(is_active=False)
    with pytest.raises(PermissionDenied):
        draft(people, college)


def test_username_case_unique_and_login(client, people):
    response = client.post(
        "/office/login/", {"username": "PROCESSOR", "password": "Synthetic-Only-7!Testing"}
    )
    assert response.status_code == 302
    with transaction.atomic(), pytest.raises(IntegrityError):
        StaffUser.objects.create(username="PROCESSOR", full_name="अन्य")


def test_login_logout_and_csrf(people):
    client = Client(enforce_csrf_checks=True)
    assert client.post("/office/login/", {}).status_code == 403
    client.force_login(people["processor"])
    assert client.get("/office/logout/").status_code == 405
    assert client.post("/office/logout/").status_code == 403
    client.get("/office/")
    response = client.post(
        "/office/logout/", {"csrfmiddlewaretoken": client.cookies["csrftoken"].value}
    )
    assert response.status_code == 302
    assert client.get("/office/").status_code == 302


def test_login_throttled(client, people):
    for _ in range(5):
        assert (
            client.post(
                "/office/login/", {"username": "processor", "password": "wrong"}
            ).status_code
            == 200
        )
    assert (
        client.post("/office/login/", {"username": "processor", "password": "wrong"}).status_code
        == 429
    )


def test_staff_creation_inactive_and_no_credentials_in_audit(client, people):
    client.force_login(people["admin"])
    response = client.post(
        "/office/staff/new/",
        {
            "username": "new.staff",
            "full_name": "नया कर्मचारी",
            "email": "",
            "roles": ["processor"],
            "reason": "स्वीकृत",
        },
    )
    assert response.status_code == 302
    user = StaffUser.objects.get(username="new.staff")
    assert not user.is_active and not user.has_usable_password()
    event = AuditEvent.objects.get(target_id=user.pk)
    assert "password" not in str(event.after)


def test_admin_cannot_self_elevate(people):
    user = people["admin"]
    with pytest.raises(PermissionDenied):
        save_staff(
            user,
            {
                "username": user.username,
                "full_name": user.full_name,
                "email": "",
                "is_active": True,
            },
            ["admin", "processor"],
            "test",
            user.pk,
        )


def test_last_active_admin_protected(people):
    # Even a stale disabled admin object cannot perform a change as an active actor.
    admin = people["admin"]
    other = people["processor"]
    RoleAssignment.objects.create(user=other, role=Role.ADMIN, reason="fixture")
    other.is_active = False
    other.save()
    with pytest.raises(PermissionDenied):
        save_staff(
            other,
            {
                "username": admin.username,
                "full_name": admin.full_name,
                "email": "",
                "is_active": False,
            },
            [],
            "test",
            admin.pk,
        )
    assert StaffUser.objects.get(pk=admin.pk).is_active


def test_referenced_records_protected(people, college):
    draft(people, college)
    with pytest.raises(ProtectedError):
        college.delete()
    with pytest.raises(ProtectedError):
        people["processor"].delete()


def test_role_constraint(people):
    with transaction.atomic(), pytest.raises(IntegrityError):
        RoleAssignment.objects.create(
            user=people["processor"], role=Role.PROCESSOR, reason="duplicate"
        )


def test_negative_count_rejected_at_database(people, college):
    obj = draft(people, college)
    with transaction.atomic(), pytest.raises(IntegrityError):
        RequestDraft.objects.filter(pk=obj.pk).update(candidate_count=-1)


def test_readonly_can_see_history_but_not_change(client, people, college):
    obj = draft(people, college)
    client.force_login(people["reviewer"])
    assert client.get(reverse("office_detail", args=["requests", obj.pk])).status_code == 200
    assert client.post(reverse("office_edit", args=["requests", obj.pk]), {}).status_code == 403


def test_directory_history_requires_master_role(client, people, college):
    client.force_login(people["processor"])
    response = client.get(reverse("office_detail", args=["institutions", college.pk]))
    assert response.status_code == 200
    assert "परिवर्तन इतिहास" not in response.content.decode()


def test_whitespace_name_rejected_by_database(people, college):
    with transaction.atomic(), pytest.raises(IntegrityError):
        Institution.objects.filter(pk=college.pk).update(name="   ")


def test_local_password_setup_audited_without_secret(people):
    from django.core.management import call_command

    user = save_staff(
        people["admin"],
        {"username": "activate.me", "full_name": "परीक्षण", "email": ""},
        [Role.PROCESSOR],
        "fixture",
    )
    with patch(
        "apps.accounts.management.commands.setup_staff.getpass",
        return_value="Unique-Local-Testing-42!",
    ):
        call_command("setup_staff", user.username)
    user.refresh_from_db()
    assert user.is_active and user.check_password("Unique-Local-Testing-42!")
    event = AuditEvent.objects.filter(target_id=user.pk).first()
    assert event.system_actor == "local-operator"
    assert "Unique-Local" not in str(event.after)


def test_role_revocation_retains_grant_reason(people):
    user = people["processor"]
    assignment = RoleAssignment.objects.get(user=user)
    save_staff(
        people["admin"],
        {"username": user.username, "full_name": user.full_name, "email": "", "is_active": True},
        [],
        "Revocation reference",
        user.pk,
    )
    assignment.refresh_from_db()
    assert assignment.reason == "Test fixture"
    assert assignment.revoked_reason == "Revocation reference"
    assert assignment.revoked_by == people["admin"]


@pytest.mark.django_db(transaction=True)
def test_concurrent_draft_edits_one_wins(people, college):
    obj = draft(people, college)
    barrier = Barrier(2)

    def change(text):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            save_record(
                people["processor"],
                RequestDraft,
                {"institution": college, "appointment_type": "subject_expert", "remarks": text},
                1,
                obj.pk,
            )
            return "saved"
        except EditConflict:
            return "conflict"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(change, ["एक", "दो"]))
    assert sorted(results) == ["conflict", "saved"]
    assert AuditEvent.objects.filter(target_id=obj.pk).count() == 2


@pytest.mark.django_db(transaction=True)
def test_concurrent_admin_disabling_cannot_remove_both(people):
    a, b = people["admin"], people["processor"]
    RoleAssignment.objects.create(user=b, role=Role.ADMIN, reason="fixture")
    barrier = Barrier(2)

    def disable(pair):
        actor, target = pair
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            save_staff(
                actor,
                {
                    "username": target.username,
                    "full_name": target.full_name,
                    "email": "",
                    "is_active": False,
                },
                [],
                "test concurrent change",
                target.pk,
            )
            return "saved"
        except (PermissionDenied, ValidationError):
            return "denied"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(disable, [(a, b), (b, a)])) == ["denied", "saved"]
    assert (
        RoleAssignment.objects.filter(
            role=Role.ADMIN, revoked_at__isnull=True, user__is_active=True
        ).count()
        == 1
    )
