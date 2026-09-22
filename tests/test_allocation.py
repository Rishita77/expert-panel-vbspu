from dataclasses import replace
from datetime import date
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError

from apps.nominations.engine import Candidate, History, allocate, demonstration, nomination_year

D = date(2026, 9, 13)


def candidate(i, count=0, last=None, category="general", reasons=()):
    return Candidate(
        str(i), f"Expert {i}", i, category, reasons, History(count, last, last is None), True
    )


def poolset():
    return {
        "vc": [candidate(1)],
        "principal": [candidate(2)],
        "professor": [candidate(i) for i in range(3, 9)],
        "scst": [candidate(9, category="sc")],
        "obc": [candidate(10, category="obc")],
    }


def test_srs_count_date_sequence_priority():
    p = poolset()
    p["professor"] = [
        candidate(10, 2, date(2026, 8, 20)),
        candidate(20, 1, date(2026, 9, 1)),
        candidate(30, 1, date(2026, 8, 1)),
        candidate(25, 1, date(2026, 8, 1)),
        candidate(40, 3, date(2026, 7, 1)),
    ]
    r = allocate("principal", p, D)
    assert [s["id"] for s in r["seats"] if s["role"] == "professor"] == [
        "25",
        "30",
        "20",
        "10",
        "40",
    ]


def test_never_first_and_lifetime_date_retained():
    p = poolset()
    p["vc"] = [candidate(22, 0, date(2025, 3, 1)), candidate(23)]
    r = allocate("principal", p, D)
    assert r["seats"][0]["id"] == "23"


@pytest.mark.parametrize(
    "history",
    [None, History(-1, D), History(1, None, True), History(0, None), History(0, date(2030, 1, 1))],
)
def test_unknown_or_contradictory_history_blocks_without_silent_skipping(history):
    p = poolset()
    p["vc"] = [replace(candidate(1), history=history), candidate(20)]
    r = allocate("principal", p, D)
    assert not r["complete"] and not r["seats"]


@pytest.mark.parametrize(
    "sc,obc,extras", [(False, False, 2), (True, False, 1), (False, True, 1), (True, True, 0)]
)
def test_srs_main_six_representation(sc, obc, extras):
    p = poolset()
    p["professor"][0] = replace(p["professor"][0], category="st" if sc else "general")
    p["professor"][1] = replace(p["professor"][1], category="obc" if obc else "general")
    p["vc"][0] = replace(p["vc"][0], category="sc")
    r = allocate("principal", p, D)
    assert r["complete"] and len(r["seats"]) == 7 + extras


def test_vc_first_collision_never_silently_backtracks():
    p = poolset()
    p["professor"] = [candidate(1), *[candidate(i) for i in range(3, 7)]]
    p["vc"].append(candidate(25))
    r = allocate("principal", p, D)
    assert r["seats"][0]["id"] == "1"
    assert not r["complete"]
    assert len({s["id"] for s in r["seats"]}) == len(r["seats"])


def test_ineligible_skipped_with_reason_not_sequence_change():
    p = poolset()
    p["vc"] = [replace(candidate(1), reasons=("own college",)), candidate(25)]
    r = allocate("principal", p, D)
    assert r["seats"][0]["id"] == "25"
    skipped = next(row for row in r["roles"][0]["rows"] if row["id"] == "1")
    assert skipped["sequence"] == 1
    assert skipped["reasons"] == ["own college"]


def test_duplicate_membership_and_missing_supplement():
    p = poolset()
    p["professor"] = [candidate(3)] * 8
    r = allocate("principal", p, D)
    assert not r["complete"]
    p = poolset()
    p["obc"] = []
    assert not allocate("principal", p, D)["complete"]


def test_deterministic_and_no_count_side_effects():
    p = poolset()
    before = repr(p)
    assert allocate("principal", p, D) == allocate("principal", p, D)
    assert repr(p) == before
    assert demonstration(D)["synthetic"] and demonstration(D)["complete"]


def test_cycles_and_provisional_policy_isolation():
    assert nomination_year(date(2026, 6, 30)) == "2025-2026"
    assert nomination_year(date(2026, 7, 1)) == "2026-2027"
    a = allocate("subject_expert", poolset(), D)
    a["policy"]["professors"] = 99
    assert allocate("principal", poolset(), D)["policy"]["professors"] == 5
    assert a["policy"]["provisional"]


@pytest.fixture
def records(db, settings):
    if settings.SETTINGS_MODULE != "config.foundation":
        pytest.skip("Persistent settings required")
    from apps.accounts.models import AccessMutex, RoleAssignment, StaffUser
    from apps.cases.models import RequestDraft
    from apps.experts.models import Appointment, Expert
    from apps.institutions.models import Institution, Subject
    from apps.panels.models import (
        ApprovalRecord,
        CandidateList,
        PoolMembership,
        PoolScope,
        PoolVersion,
    )

    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    AccessMutex.objects.get_or_create(pk=1)
    users = {}
    for role in ["processor", "reviewer", "master", "admin"]:
        u = StaffUser.objects.create_user(
            username=role, full_name=role, password="Test-Only-123!", is_active=True
        )
        RoleAssignment.objects.create(user=u, role=role, reason="test")
        users[role] = u
    actor = users["processor"]
    tracked = {"created_by": actor, "updated_by": actor}
    college = Institution.objects.create(name="Requesting", institution_kind="college", **tracked)
    home = Institution.objects.create(
        name="Other",
        institution_kind="college",
        management_type="aided",
        is_affiliated_to_vbspu=True,
        **tracked,
    )
    subject = Subject.objects.create(name="Hindi", **tracked)
    case = RequestDraft.objects.create(
        institution=college,
        subject=subject,
        appointment_type="principal",
        state=RequestDraft.State.SUBMITTED,
        **tracked,
    )
    expert = Expert.objects.create(name="Real expert", category="sc", **tracked)
    expert.subjects.add(subject)
    appointment = Appointment.objects.create(
        expert=expert,
        institution=home,
        administrative_post="principal",
        academic_designation="professor",
        classification="internal",
        evidence="verified",
        **tracked,
    )
    approval = ApprovalRecord.objects.create(
        authority="EC",
        authority_type="ec",
        reference="TEST",
        approval_date=date(2026, 7, 1),
        **tracked,
    )
    pool = PoolVersion.objects.create(
        candidate_list=CandidateList.objects.create(**tracked),
        title="VC",
        nominee_role="vc",
        approval=approval,
        effective_date=date(2026, 7, 1),
        valid_through=date(2027, 6, 30),
        **tracked,
    )
    PoolScope.objects.create(pool=pool, appointment_type="principal", subject=subject, **tracked)
    member = PoolMembership.objects.create(pool=pool, expert=expert, **tracked)
    pool.state = "approved"
    pool.save()
    return users, case, expert, appointment, pool, member


def test_real_history_unknown_and_run_immutable(records):
    from django.db import IntegrityError, transaction

    from apps.nominations.models import AllocationRun
    from apps.nominations.services import generate

    users, case, expert, *_ = records
    run = generate(users["reviewer"], case.pk, case.revision)
    assert not run.snapshot["complete"] and not run.snapshot["seats"]
    assert run.snapshot["roles"][0]["rows"][0]["count"] is None
    with transaction.atomic(), pytest.raises(IntegrityError):
        AllocationRun.objects.filter(pk=run.pk).update(snapshot={})
    expert.name = "Changed later"
    expert.save()
    run.refresh_from_db()
    assert run.snapshot["candidate_evidence"][0]["name"] == "Real expert"


@pytest.mark.parametrize("status", ["retired", "transferred"])
def test_permanent_inactivity_verifier_no_upload_or_reactivation(records, status):
    from django.core.exceptions import ValidationError
    from django.db import IntegrityError, transaction

    from apps.experts.models import Expert
    from apps.experts.services import save_expert
    from apps.nominations.models import Assessment
    from apps.nominations.services import assess

    users, case, expert, *_ = records
    a = assess(
        users["processor"],
        case.pk,
        expert.pk,
        {
            "status": status,
            "conflict": False,
            "verifier": "Officer who verified",
            "reason": "Telephone confirmation",
        },
        case.revision,
    )
    assert a.verifier != a.recorded_by.full_name
    expert.refresh_from_db()
    assert not expert.is_active
    with pytest.raises(ValidationError):
        save_expert(
            users["master"], {"is_active": True, "reason": "Try"}, expert.revision, expert.pk
        )
    with transaction.atomic(), pytest.raises(IntegrityError):
        Expert.objects.filter(pk=expert.pk).update(is_active=True)
    with transaction.atomic(), pytest.raises(IntegrityError):
        Assessment.objects.filter(pk=a.pk).delete()


def test_status_and_audit_roll_back_together(records):
    from apps.nominations.models import Assessment
    from apps.nominations.services import assess

    users, case, expert, *_ = records
    with (
        patch("apps.nominations.services.record", side_effect=RuntimeError),
        pytest.raises(RuntimeError),
    ):
        assess(
            users["processor"],
            case.pk,
            expert.pk,
            {"status": "retired", "conflict": False, "verifier": "Officer", "reason": "Test"},
            case.revision,
        )
    expert.refresh_from_db()
    assert expert.is_active and not Assessment.objects.exists()


def test_allocation_date_only_and_own_college_all_roles(records):
    from apps.nominations.services import candidate_facts

    users, case, expert, appointment, pool, member = records
    case.selection_date = date(2030, 1, 1)
    assert not candidate_facts(member, case, D, None, set())[0].reasons
    appointment.institution = case.institution
    appointment.save()
    assert any("महाविद्यालय" in x for x in candidate_facts(member, case, D, None, set())[0].reasons)


def test_unavailability_and_conflict_preserve_master(records):
    from apps.nominations.services import assess, candidate_facts

    users, case, expert, _, _, member = records
    a = assess(
        users["processor"],
        case.pk,
        expert.pk,
        {
            "status": "unavailable",
            "conflict": True,
            "verifier": "Officer",
            "reason": "Related to candidate",
        },
        case.revision,
    )
    person, _ = candidate_facts(member, case, D, a, set())
    assert len(person.reasons) == 2
    expert.refresh_from_db()
    assert expert.is_active


def test_access_stale_revision_and_csrf(records, client):
    from django.test import Client

    from apps.nominations.models import AllocationRun

    users, case, *_ = records
    url = f"/office/allocation/request/{case.pk}/"
    for role in ["admin", "master"]:
        client.force_login(users[role])
        assert client.get(url).status_code == 403
    client.force_login(users["reviewer"])
    assert client.get(url).status_code == 200
    assert client.post(url, {"action": "generate", "revision": 1}).status_code == 302
    client.force_login(users["processor"])
    assert client.post(url, {"action": "generate", "revision": 1}).status_code == 403
    client.force_login(users["reviewer"])
    assert client.post(url, {"action": "generate", "revision": 999}).status_code == 409
    assert AllocationRun.objects.exists()
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(users["reviewer"])
    assert csrf.post(url, {"action": "generate", "revision": 1}).status_code == 403


def test_poc_submits_request_and_reviewer_returns_or_generates(records, client):
    from apps.cases.models import RequestDraft

    users, case, *_ = records
    case.state = RequestDraft.State.DRAFT
    case.save(update_fields=["state"])
    detail_url = f"/office/requests/{case.pk}/"
    workbench_url = f"/office/allocation/request/{case.pk}/"

    client.force_login(users["processor"])
    assert (
        client.post(detail_url, {"action": "submit", "revision": case.revision}).status_code == 302
    )
    case.refresh_from_db()
    assert case.state == RequestDraft.State.SUBMITTED
    assert (
        client.post(workbench_url, {"action": "generate", "revision": case.revision}).status_code
        == 403
    )

    client.force_login(users["reviewer"])
    assert (
        client.post(
            detail_url,
            {"action": "return", "revision": case.revision, "reason": "विषय जाँचें"},
        ).status_code
        == 302
    )
    case.refresh_from_db()
    assert case.state == RequestDraft.State.RETURNED

    client.force_login(users["processor"])
    assert (
        client.post(detail_url, {"action": "submit", "revision": case.revision}).status_code == 302
    )
    client.force_login(users["reviewer"])
    assert (
        client.post(workbench_url, {"action": "generate", "revision": case.revision}).status_code
        == 302
    )
    case.refresh_from_db()
    assert case.state == RequestDraft.State.OFFERED


def test_approved_pool_overlap_rejected(records):
    from django.core.exceptions import ValidationError

    from apps.panels.models import CandidateList, PoolMembership, PoolScope, PoolVersion
    from apps.panels.services import approve_pool

    users, case, expert, _, old, _ = records
    tracked = {"created_by": users["master"], "updated_by": users["master"]}
    pool = PoolVersion.objects.create(
        candidate_list=CandidateList.objects.create(**tracked),
        title="Duplicate",
        nominee_role="vc",
        approval=old.approval,
        effective_date=old.effective_date,
        valid_through=old.valid_through,
        **tracked,
    )
    PoolScope.objects.create(pool=pool, appointment_type="principal", all_subjects=True, **tracked)
    PoolMembership.objects.create(pool=pool, expert=expert, **tracked)
    with pytest.raises(ValidationError, match="पहले से"):
        approve_pool(users["master"], pool.pk, pool.revision, "Test")


def test_allocation_uses_expert_directory_not_candidate_list_scope(records):
    from apps.nominations.services import generate
    from apps.panels.models import PoolScope, PoolVersion

    users, case, _, _, pool, _ = records
    # Use another draft list to create crossed scopes, then record its approved state.
    from apps.panels.models import CandidateList

    tracked = {"created_by": users["master"], "updated_by": users["master"]}
    p = PoolVersion.objects.create(
        candidate_list=CandidateList.objects.create(**tracked),
        title="Crossed",
        nominee_role="professor",
        approval=pool.approval,
        effective_date=pool.effective_date,
        valid_through=pool.valid_through,
        **tracked,
    )
    from apps.institutions.models import Subject

    other = Subject.objects.create(name="Other subject", **tracked)
    PoolScope.objects.create(pool=p, appointment_type="principal", subject=other, **tracked)
    PoolScope.objects.create(pool=p, appointment_type="hod", subject=case.subject, **tracked)
    p.state = "approved"
    p.save()
    r = generate(users["reviewer"], case.pk, case.revision)
    assert all(s["source"] == "expert_master" for s in r.snapshot["sources"])


def test_verified_history_adapter_feeds_same_ranker(records):
    from apps.nominations.services import generate

    users, case, expert, *_ = records
    with patch(
        "apps.nominations.services.verified_history",
        return_value={str(expert.pk): History(0, None, True)},
    ):
        run = generate(users["reviewer"], case.pk, case.revision)
    assert run.snapshot["seats"][0]["id"] == str(expert.pk)
    assert not run.snapshot["complete"]  # Other required sources still absent.


@pytest.mark.django_db(transaction=True)
def test_simultaneous_evaluations_do_not_reserve_or_change_inputs(records):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections

    from apps.nominations.services import generate

    users, case, expert, *_ = records
    barrier = Barrier(2)

    def worker():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            run = generate(users["reviewer"], case.pk, case.revision)
            return run.pk, run.snapshot
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: worker(), range(2)))
    assert results[0][0] != results[1][0]
    assert results[0][1] == results[1][1]
    expert.refresh_from_db()
    assert expert.is_active


@pytest.fixture
def complete_offer(records):
    from django.utils import timezone

    from apps.experts.models import Expert
    from apps.nominations.models import AllocationRun

    users, case, expert, *_ = records
    experts = [expert]
    for number, category in enumerate(["general", "general", "sc", "obc", "general", "general"], 2):
        experts.append(
            Expert.objects.create(
                name=f"Final expert {number}",
                category=category,
                created_by=users["master"],
                updated_by=users["master"],
            )
        )
    roles = ["vc", "principal", "professor", "professor", "professor", "professor", "professor"]
    seats = [
        {
            "id": str(person.pk),
            "role": role,
            "name": person.name,
            "sequence": person.sequence,
            "category": person.category,
        }
        for person, role in zip(experts, roles, strict=True)
    ]
    run = AllocationRun.objects.create(
        request=case,
        request_revision=case.revision,
        created_by=users["processor"],
        allocation_date=timezone.localdate(),
        snapshot={
            "complete": True,
            "seats": seats,
            "allocation_date": timezone.localdate().isoformat(),
            "candidate_evidence": [
                {"expert": str(person.pk), "home": {"institution": "another-college"}}
                for person in experts
            ],
        },
    )
    return users, case, experts, run


def fill_final_selection(users, selection, expert_ids):
    from apps.nominations.services import save_final_selection

    return save_final_selection(
        users["processor"],
        selection.pk,
        {
            "revision": selection.revision,
            "management_reference": "MC-1",
            "management_date": D,
            "vc_reference": "VC-1",
            "vc_date": D,
        },
        expert_ids,
    )


def add_available_assessments(users, case, experts):
    from django.utils import timezone

    from apps.nominations.models import Assessment

    for expert in experts:
        Assessment.objects.create(
            request=case,
            request_revision=case.revision,
            expert=expert,
            allocation_date=timezone.localdate(),
            status="available",
            conflict=False,
            verifier="Reviewer evidence",
            reason="Confirmed",
            recorded_by=users["processor"],
        )


def test_final_selection_provisional_shape_submit_return_and_lock(complete_offer):
    from apps.nominations.models import FinalSelection, UtilisationEntry
    from apps.nominations.services import (
        create_final_selection,
        lock_final_selection,
        return_final_selection,
        submit_final_selection,
    )

    users, case, experts, run = complete_offer
    selection = create_final_selection(users["processor"], run.pk)
    assert selection.state == FinalSelection.State.DRAFT
    # VC, Principal, then four of the five offered Professors. SC and OBC are both included.
    selection = fill_final_selection(
        users,
        selection,
        [
            member.pk
            for member in selection.members.order_by("position")
            if member.role != "professor" or member.position < 5
        ],
    )
    selection = submit_final_selection(users["processor"], selection.pk, selection.revision)
    with pytest.raises(ValidationError, match="कारण"):
        return_final_selection(users["reviewer"], selection.pk, selection.revision, "")
    selection = return_final_selection(
        users["reviewer"], selection.pk, selection.revision, "Need a clearer reference"
    )
    assert selection.state == FinalSelection.State.RETURNED
    selection = fill_final_selection(
        users,
        selection,
        [
            member.pk
            for member in selection.members.order_by("position")
            if member.role != "professor" or member.position < 5
        ],
    )
    selection = submit_final_selection(users["processor"], selection.pk, selection.revision)
    add_available_assessments(users, case, experts)
    locked = lock_final_selection(users["reviewer"], selection.pk, selection.revision, "Verified")
    assert locked.state == FinalSelection.State.LOCKED
    assert UtilisationEntry.objects.filter(selection=locked).count() == 6
    assert lock_final_selection(users["reviewer"], locked.pk, locked.revision).pk == locked.pk
    assert UtilisationEntry.objects.filter(selection=locked).count() == 6


def test_final_lock_blocks_missing_category_or_assessment(complete_offer):
    from apps.nominations.services import (
        create_final_selection,
        lock_final_selection,
        submit_final_selection,
    )

    users, case, experts, run = complete_offer
    selection = create_final_selection(users["processor"], run.pk)
    # Exclude the SC professor from the four main final choices.
    chosen = [
        member.pk
        for member in selection.members.order_by("position")
        if member.role != "professor" or member.position in {1, 3, 4, 5}
    ]
    selection = fill_final_selection(users, selection, chosen)
    with pytest.raises(ValidationError, match="SC/ST"):
        submit_final_selection(users["processor"], selection.pk, selection.revision)
    # Restore category coverage, submit, then lock still refuses missing availability checks.
    chosen = [
        member.pk
        for member in selection.members.order_by("position")
        if member.role != "professor" or member.position < 5
    ]
    selection = fill_final_selection(users, selection, chosen)
    selection = submit_final_selection(users["processor"], selection.pk, selection.revision)
    with pytest.raises(ValidationError, match="सत्यापन शेष"):
        lock_final_selection(users["reviewer"], selection.pk, selection.revision)


def test_final_lock_rejects_processor_and_database_changes(complete_offer):
    from django.db import IntegrityError, transaction

    from apps.nominations.models import FinalMember, FinalSelection, UtilisationEntry
    from apps.nominations.services import (
        create_final_selection,
        lock_final_selection,
        submit_final_selection,
    )

    users, case, experts, run = complete_offer
    selection = create_final_selection(users["processor"], run.pk)
    selection = fill_final_selection(
        users,
        selection,
        [
            member.pk
            for member in selection.members.order_by("position")
            if member.role != "professor" or member.position < 5
        ],
    )
    selection = submit_final_selection(users["processor"], selection.pk, selection.revision)
    add_available_assessments(users, case, experts)
    with pytest.raises(Exception):
        lock_final_selection(users["processor"], selection.pk, selection.revision)
    selection = lock_final_selection(users["reviewer"], selection.pk, selection.revision)
    with transaction.atomic(), pytest.raises(IntegrityError):
        FinalSelection.objects.filter(pk=selection.pk).update(state="draft")
    member = FinalMember.objects.filter(selection=selection, selected=True).first()
    with transaction.atomic(), pytest.raises(IntegrityError):
        FinalMember.objects.filter(pk=member.pk).update(selected=False)
    entry = UtilisationEntry.objects.get(member=member)
    with transaction.atomic(), pytest.raises(IntegrityError):
        UtilisationEntry.objects.filter(pk=entry.pk).delete()


def test_fresh_start_history_and_confirmed_cancellation_reverse_active_entries(complete_offer):
    from django.utils import timezone

    from apps.nominations.history import verified_history
    from apps.nominations.models import TrackingBaseline, UtilisationEntry
    from apps.nominations.services import (
        confirm_panel_change,
        create_cancellation_change,
        create_final_selection,
        submit_final_selection,
        submit_panel_change,
    )

    users, case, experts, run = complete_offer
    selection = create_final_selection(users["processor"], run.pk)
    selection = fill_final_selection(
        users,
        selection,
        [
            member.pk
            for member in selection.members.order_by("position")
            if member.role != "professor" or member.position < 5
        ],
    )
    selection = submit_final_selection(users["processor"], selection.pk, selection.revision)
    add_available_assessments(users, case, experts)
    from apps.nominations.services import lock_final_selection

    selection = lock_final_selection(users["reviewer"], selection.pk, selection.revision)
    TrackingBaseline.objects.create(
        start_date=timezone.localdate(),
        approval_reference="GO-LIVE",
        is_active=True,
        activated_by=users["admin"],
    )
    history = verified_history([str(experts[0].pk)], timezone.localdate())
    assert history[str(experts[0].pk)].annual_count == 1
    change = create_cancellation_change(
        users["processor"], selection.pk, "कार्य नहीं हुआ", "Officer", True
    )
    change = submit_panel_change(users["processor"], change.pk, change.revision, {})
    change = confirm_panel_change(users["reviewer"], change.pk, change.revision)
    assert change.state == "confirmed"
    assert not UtilisationEntry.objects.filter(selection=selection, reversal__isnull=True).exists()
    history = verified_history([str(experts[0].pk)], timezone.localdate())
    assert history[str(experts[0].pk)].annual_count == 0
    assert history[str(experts[0].pk)].verified_never


def test_letter_approval_freezes_pdf_without_changing_utilisation(
    complete_offer, settings, tmp_path
):
    from django.core.exceptions import ValidationError

    from apps.nominations.models import Letter, LetterRevision, UtilisationEntry
    from apps.nominations.services import approve_letter, create_letter, submit_letter

    users, case, _experts, run = complete_offer
    settings.PRIVATE_DOCUMENT_ROOT = tmp_path / "private"
    revision = create_letter(users["processor"], "offer", run.pk, "OUT/ 01", D)
    assert revision.snapshot["members"] == run.snapshot["seats"]
    with pytest.raises(ValidationError, match="पत्रांक"):
        create_letter(users["processor"], "offer", run.pk, "out/ 01", D)
    revision = submit_letter(users["processor"], revision.pk, revision.revision)
    with patch("apps.nominations.services.render_letter_pdf", return_value=b"frozen-pdf"):
        revision = approve_letter(users["reviewer"], revision.pk, revision.revision)
    assert revision.state == LetterRevision.State.APPROVED
    assert (settings.PRIVATE_DOCUMENT_ROOT / revision.pdf_key).read_bytes() == b"frozen-pdf"
    assert revision.checksum
    assert UtilisationEntry.objects.filter(selection__request=case).count() == 0
    with pytest.raises(Exception):
        Letter.objects.filter(pk=revision.letter_id).update(reference="changed")


def test_letter_renderer_creates_a_pdf(complete_offer):
    from apps.nominations.services import create_letter, render_letter_pdf

    users, _case, _experts, run = complete_offer
    revision = create_letter(users["processor"], "offer", run.pk, "RENDER/01", D)
    assert render_letter_pdf(revision).startswith(b"%PDF")
