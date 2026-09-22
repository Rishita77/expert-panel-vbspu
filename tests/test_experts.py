import csv
import io
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier
from unittest.mock import patch

import pytest
from django.conf import settings

if settings.SETTINGS_MODULE != "config.foundation":
    pytest.skip("PostgreSQL foundation settings required.", allow_module_level=True)

from django.core.exceptions import ValidationError  # noqa: E402
from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from django.db import IntegrityError, close_old_connections, connection, transaction  # noqa: E402
from django.urls import reverse  # noqa: E402

from apps.accounts.models import AccessMutex, Role, RoleAssignment, StaffUser  # noqa: E402
from apps.audit.models import AuditEvent  # noqa: E402
from apps.cases.services import EditConflict, save_record  # noqa: E402
from apps.experts.import_preview import SCHEMAS, validate_csv  # noqa: E402
from apps.experts.models import Appointment, Expert  # noqa: E402
from apps.experts.services import save_appointment, save_expert  # noqa: E402
from apps.institutions.models import Institution, Subject  # noqa: E402
from apps.panels.checks import expert_issues, pool_issues  # noqa: E402
from apps.panels.models import ApprovalRecord, PoolMembership, PoolScope, PoolVersion  # noqa: E402
from apps.panels.services import approve_pool, new_version, save_pool_record  # noqa: E402

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    AccessMutex.objects.get_or_create(pk=1)
    users = {}
    for role in Role.values:
        user = StaffUser.objects.create_user(
            username="expert_" + role, full_name=role, password="TestOnly-7!", is_active=True
        )
        RoleAssignment.objects.create(user=user, role=role, reason="test")
        users[role] = user
    school = save_record(
        users["master"],
        Institution,
        {
            "name": "परीक्षण कॉलेज A",
            "institution_kind": "college",
            "management_type": "aided",
            "is_affiliated_to_vbspu": True,
        },
        0,
    )
    subject = save_record(users["master"], Subject, {"name": "हिन्दी"}, 0)
    return users, school, subject


def make_expert(setup, name="प्राचार्य प्रोफेसर परीक्षण", category="sc"):
    users, school, subject = setup
    expert = save_expert(
        users["master"],
        {
            "name": name,
            "category": category,
            "mobile": "+919999999991",
            "email": "private@example.test",
            "subjects": [subject],
        },
    )
    save_appointment(
        users["master"],
        expert.pk,
        {
            "institution": school,
            "administrative_post": "principal",
            "academic_designation": "professor",
            "evidence": "Verified record",
            "classification": "internal",
            "start_date": date(2020, 1, 1),
            "is_current": True,
            "expert_revision": expert.revision,
        },
    )
    expert.refresh_from_db()
    return expert


def make_pool(setup, expert=None, role="professor"):
    users, _, subject = setup
    approval = save_pool_record(
        users["master"],
        ApprovalRecord,
        {
            "authority": "कार्य परिषद्",
            "authority_type": "ec",
            "reference": "TEST-2026",
            "approval_date": date(2026, 7, 1),
        },
    )
    pool = save_pool_record(
        users["master"],
        PoolVersion,
        {
            "title": "परीक्षण सूची",
            "nominee_role": role,
            "approval": approval,
            "effective_date": date(2026, 7, 1),
            "valid_through": date(2027, 6, 30),
        },
    )
    save_pool_record(
        users["master"],
        PoolScope,
        {"appointment_type": "subject_expert", "subject": subject, "all_subjects": False},
        parent=pool.pk,
    )
    if expert:
        save_pool_record(
            users["master"], PoolMembership, {"expert": expert, "is_active": True}, parent=pool.pk
        )
    pool.refresh_from_db()
    return pool


def test_one_person_multiple_roles_one_sequence(setup):
    users, _, _ = setup
    expert = make_expert(setup)
    assert expert.sequence > 0
    for role in ["principal", "professor", "vc"]:
        pool = make_pool(setup, expert, role)
        assert not pool_issues(pool)
        approve_pool(users["master"], pool.pk, pool.revision, "Recorded EC reference")
    assert Expert.objects.count() == 1
    assert expert.memberships.count() == 3


def test_sequence_immutable_even_direct_database_update(setup):
    expert = make_expert(setup)
    with transaction.atomic(), pytest.raises(IntegrityError):
        Expert.objects.filter(pk=expert.pk).update(sequence=expert.sequence + 100)


def test_service_rejects_sequence_input(setup):
    users, _, _ = setup
    with pytest.raises(ValidationError):
        save_expert(users["master"], {"name": "test", "sequence": 9})


def test_name_only_remains_incomplete(client, setup):
    users, _, _ = setup
    expert = save_expert(users["master"], {"name": "अधूरा रिकॉर्ड"})
    assert expert.category is None
    assert expert_issues(expert)
    client.force_login(users["processor"])
    text = client.get(reverse("expert_detail", args=["experts", expert.pk])).content.decode()
    assert "इतिहास अभी लोड नहीं हुआ है" in text


def test_new_expert_can_include_current_institution_and_post(setup):
    users, school, _ = setup
    expert = save_expert(
        users["master"],
        {
            "name": "नई विशेषज्ञ",
            "institution": school,
            "administrative_post": "principal",
            "administrative_post_title": "",
            "academic_designation": "professor",
            "post_end_date": None,
        },
    )
    appointment = expert.appointments.get()
    assert appointment.institution == school
    assert appointment.administrative_post == "principal"
    assert appointment.is_current


def test_new_expert_form_collects_academic_designation_and_optional_post(client, setup):
    users, school, subject = setup
    client.force_login(users["master"])
    response = client.post(
        reverse("expert_new", args=["experts"]),
        {
            "name": "फॉर्म विशेषज्ञ",
            "category": "general",
            "institution": school.pk,
            "academic_designation": "professor",
            "subjects": [subject.pk],
            "holds_administrative_post": "no",
            "administrative_post": "",
            "administrative_post_title": "",
            "post_end_date": "",
            "is_active": "on",
            "revision": 0,
        },
    )
    assert response.status_code == 302
    appointment = Expert.objects.get(name="फॉर्म विशेषज्ञ").appointments.get()
    assert appointment.academic_designation == "professor"
    assert appointment.administrative_post == ""
    assert appointment.post_end_date is None


def test_same_name_not_merged(setup):
    a, b = make_expert(setup), make_expert(setup)
    assert a.pk != b.pk and a.sequence != b.sequence


def test_transfer_preserves_history_and_identity(setup):
    users, school, _ = setup
    expert = make_expert(setup)
    sequence = expert.sequence
    b = save_record(users["master"], Institution, {"name": "B", "institution_kind": "college"}, 0)
    save_appointment(
        users["master"],
        expert.pk,
        {
            "institution": b,
            "administrative_post": "",
            "academic_designation": "professor",
            "evidence": "Transfer letter",
            "classification": "external",
            "start_date": date(2026, 10, 1),
            "is_current": True,
            "reason": "Transfer",
            "expert_revision": expert.revision,
        },
    )
    previous = expert.appointments.get(institution=school)
    assert not previous.is_current and previous.end_date == date(2026, 10, 1)
    assert expert.appointments.filter(is_current=True).count() == 1
    expert.refresh_from_db()
    assert expert.sequence == sequence


def test_overlapping_and_reversed_dates_rejected(setup):
    users, school, _ = setup
    expert = make_expert(setup)
    for start, end in [(date(2021, 1, 1), date(2020, 1, 1)), (date(2021, 1, 1), date(2022, 1, 1))]:
        with pytest.raises(ValidationError):
            save_appointment(
                users["master"],
                expert.pk,
                {
                    "institution": school,
                    "administrative_post": "",
                    "is_current": False,
                    "start_date": start,
                    "end_date": end,
                    "expert_revision": expert.revision,
                },
            )
    assert expert.appointments.count() == 1


def test_one_current_database_constraint(setup):
    users, school, _ = setup
    expert = make_expert(setup)
    with transaction.atomic(), pytest.raises(IntegrityError):
        Appointment.objects.create(
            expert=expert,
            institution=school,
            administrative_post="principal",
            is_current=True,
            created_by=users["master"],
            updated_by=users["master"],
        )


def test_own_college_exclusion_and_vc_classification(setup):
    _, school, _ = setup
    expert = make_expert(setup)
    assert any("वर्जित" in text for text in expert_issues(expert, "vc", school))
    school.management_type = "other"
    school.save()
    assert any("राजकीय" in text for text in expert_issues(expert, "vc"))


def test_principal_not_automatically_professor(setup):
    expert = make_expert(setup)
    expert.appointments.update(academic_designation="unknown")
    assert not expert_issues(expert, "principal")
    assert expert_issues(expert, "professor")
    assert expert_issues(expert, "vc")


def test_assistant_supplement_only(setup):
    expert = make_expert(setup)
    expert.appointments.update(administrative_post="", academic_designation="assistant")
    assert not expert_issues(expert, "scst")
    assert expert_issues(expert, "professor")
    assert expert_issues(expert, "vc")


def test_unverified_designation_can_be_collected_before_evidence(setup):
    users, school, _ = setup
    expert = save_expert(users["master"], {"name": "A"})
    save_appointment(
        users["master"],
        expert.pk,
        {
            "institution": school,
            "administrative_post": "principal",
            "academic_designation": "professor",
            "expert_revision": expert.revision,
        },
    )
    assert expert_issues(expert, "professor")


@pytest.mark.parametrize(
    "role,code,contact",
    [
        ("admin", 403, False),
        ("reviewer", 200, False),
        ("processor", 200, True),
        ("master", 200, True),
    ],
)
def test_contact_access_including_audit(client, setup, role, code, contact):
    users, _, _ = setup
    expert = make_expert(setup)
    client.force_login(users[role])
    response = client.get(reverse("expert_detail", args=["experts", expert.pk]))
    assert response.status_code == code
    assert ("private@example.test" in response.content.decode()) == contact
    assert ("+919999999991" in response.content.decode()) == contact


def test_processor_cannot_edit_or_import(client, setup):
    users, _, _ = setup
    client.force_login(users["processor"])
    assert client.post(reverse("expert_new", args=["experts"]), {}).status_code == 403
    assert client.get(reverse("expert_import")).status_code == 403


def test_audit_rollback_on_expert_failure(setup):
    users, _, _ = setup
    with patch("apps.experts.services.record", side_effect=RuntimeError("audit unavailable")):
        with pytest.raises(RuntimeError):
            save_expert(users["master"], {"name": "rollback"})
    assert not Expert.objects.exists()


def test_list_versioning_preserves_all_old_records(setup):
    users, _, _ = setup
    expert = make_expert(setup)
    pool = make_pool(setup, expert)
    approve_pool(users["master"], pool.pk, pool.revision, "Official approval")
    pool.refresh_from_db()
    with pytest.raises(ValidationError):
        save_pool_record(
            users["master"],
            PoolVersion,
            {"title": "illegal", "reason": "test"},
            pool.revision,
            pool.pk,
        )
    clone = new_version(users["master"], pool.pk, pool.revision, "Updated reference")
    assert clone.version == 2 and clone.state == "draft"
    assert clone.memberships.get().expert_id == expert.pk
    assert clone.scopes.count() == 1
    approve_pool(users["master"], clone.pk, clone.revision, "New official version")
    pool.refresh_from_db()
    assert pool.state == "superseded"
    assert pool.memberships.count() == 1


def test_approved_children_and_evidence_database_guards(setup):
    users, _, _ = setup
    pool = make_pool(setup, make_expert(setup))
    approve_pool(users["master"], pool.pk, pool.revision, "Recorded")
    for model, pk, data in [
        (PoolVersion, pool.pk, {"title": "tamper"}),
        (PoolMembership, pool.memberships.get().pk, {"is_active": False}),
        (PoolScope, pool.scopes.get().pk, {"appointment_type": "hod"}),
        (ApprovalRecord, pool.approval_id, {"reference": "changed"}),
    ]:
        with transaction.atomic(), pytest.raises(IntegrityError):
            model.objects.filter(pk=pk).update(**data)


def test_duplicate_membership_rejected(setup):
    users, _, _ = setup
    expert = make_expert(setup)
    pool = make_pool(setup, expert)
    with pytest.raises(ValidationError):
        save_pool_record(users["master"], PoolMembership, {"expert": expert}, parent=pool.pk)


def test_dates_and_missing_scope_block_approval(setup):
    users, _, _ = setup
    pool = make_pool(setup)
    with pytest.raises(ValidationError):
        approve_pool(users["master"], pool.pk, pool.revision, "no members")
    assert pool_issues(pool, date(2028, 1, 1))
    expert = make_expert(setup)
    with pytest.raises(ValidationError):
        save_pool_record(
            users["master"],
            PoolMembership,
            {"expert": expert, "valid_from": date(2026, 1, 1)},
            parent=pool.pk,
        )


def csv_bytes(kind, rows):
    output = io.StringIO()
    writer = csv.DictWriter(output, SCHEMAS[kind])
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def test_import_preview_no_writes_or_sequence_consumption(client, setup):
    users, _, _ = setup
    make_expert(setup)
    client.force_login(users["master"])
    before = (Expert.objects.count(), AuditEvent.objects.count())
    with connection.cursor() as cursor:
        cursor.execute("SELECT last_value FROM experts_permanent_sequence")
        sequence = cursor.fetchone()[0]
    raw = csv_bytes("experts", [{"source_key": "x", "name": "नया हिन्दी नाम", "category": "sc"}])
    response = client.post(
        reverse("expert_import"),
        {
            "kind": "experts",
            "file": SimpleUploadedFile("experts.csv", raw, content_type="text/csv"),
        },
    )
    assert response.status_code == 200
    assert "नया हिन्दी नाम" in response.content.decode()
    assert before == (Expert.objects.count(), AuditEvent.objects.count())
    with connection.cursor() as cursor:
        cursor.execute("SELECT last_value FROM experts_permanent_sequence")
        assert cursor.fetchone()[0] == sequence


def test_csv_duplicates_missing_matches_and_wrong_category(setup):
    rows = validate_csv(
        "experts",
        csv_bytes(
            "experts",
            [
                {"source_key": "x", "name": "A", "category": "wrong"},
                {"source_key": "x", "name": "B", "subject_ids": "invalid"},
            ],
        ),
    )
    assert rows[0]["errors"] and rows[1]["errors"]
    with pytest.raises(ValidationError):
        validate_csv("experts", b"name\nWrong headers")
    with pytest.raises(ValidationError):
        validate_csv("experts", b"x" * 250001)


def test_unknown_end_not_unlimited(setup):
    users, _, _ = setup
    pool = make_pool(setup, make_expert(setup))
    pool = save_pool_record(
        users["master"],
        PoolVersion,
        {"valid_through": None, "reason": "Unclear end date"},
        pool.revision,
        pool.pk,
    )
    assert any("वैधता अन्तिम" in text for text in pool_issues(pool))


def test_import_strict_dates_and_field_lengths(setup):
    result = validate_csv(
        "approvals",
        csv_bytes(
            "approvals",
            [
                {
                    "authority": "A" * 201,
                    "authority_type": "ec",
                    "reference": "test",
                    "approval_date": "20260701",
                }
            ],
        ),
    )
    assert len(result[0]["errors"]) >= 2


def test_import_detects_cross_row_scope_conflict(setup):
    _, _, subject = setup
    pool = make_pool(setup)
    result = validate_csv(
        "scopes",
        csv_bytes(
            "scopes",
            [
                {"pool_id": str(pool.pk), "appointment_type": "principal", "all_subjects": "true"},
                {
                    "pool_id": str(pool.pk),
                    "appointment_type": "principal",
                    "all_subjects": "false",
                    "subject_id": str(subject.pk),
                },
            ],
        ),
    )
    assert result[1]["errors"]


def test_missing_pool_action_is_404(client, setup):
    from uuid import uuid4

    client.force_login(setup[0]["master"])
    assert client.post(reverse("pool_action", args=[uuid4(), "approve"]), {}).status_code == 404


@pytest.mark.django_db(transaction=True)
def test_concurrent_home_changes_detect_stale_expert(setup):
    users, school, _ = setup
    expert = make_expert(setup)
    barrier = Barrier(2)

    def change(day):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            save_appointment(
                users["master"],
                expert.pk,
                {
                    "institution": school,
                    "administrative_post": "principal",
                    "start_date": date(2026, 10, day),
                    "is_current": True,
                    "reason": "Concurrent change",
                    "expert_revision": expert.revision,
                },
            )
            return "saved"
        except EditConflict:
            return "stale"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(change, [1, 2])) == ["saved", "stale"]
    assert expert.appointments.filter(is_current=True).count() == 1
