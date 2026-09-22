from dataclasses import FrozenInstanceError

import pytest
from django.test import Client
from django.urls import reverse

from apps.nominations.policies import POLICIES
from apps.workspace.forms import IntakePreviewForm


@pytest.mark.parametrize("name", ["home", "intake", "policies", "health"])
def test_preview_pages_do_not_require_database(client, name):
    response = client.get(reverse(name))
    assert response.status_code == 200
    assert response["Cache-Control"] == "no-store"
    assert response["X-Robots-Tag"] == "noindex, nofollow"


def test_hindi_and_mixed_script_survive_preview(client):
    response = client.post(
        reverse("intake"),
        {
            "college_name": "परीक्षण महाविद्यालय — जौनपुर",
            "subject": "हिन्दी / Political Science",
            "contact_details": "डॉ. परीक्षण शर्मा",
            "appointment_type": "subject_expert",
            "candidate_count": "0",
            "selection_date": "2026-09-30",
        },
    )
    assert response.status_code == 200
    text = response.content.decode()
    assert "परीक्षण महाविद्यालय — जौनपुर" in text
    assert "हिन्दी / Political Science" in text
    assert "डॉ. परीक्षण शर्मा" in text
    assert "30.09.2026" in text
    assert "कुलपति की पुष्टि शेष" in text
    assert "सहेजा गया या जमा किया गया आवेदन नहीं" in text


def test_untrusted_text_is_escaped(client):
    response = client.post(reverse("intake"), {"college_name": '<script>alert("x")</script>'})
    text = response.content.decode()
    assert '<script>alert("x")</script>' not in text
    assert "&lt;script&gt;" in text


@pytest.mark.parametrize(
    "data",
    [
        {"appointment_type": "invented"},
        {"candidate_count": "-1"},
        {"candidate_count": "2.4"},
        {"selection_date": "2026-02-30"},
        {"college_name": "अ" * 256},
    ],
)
def test_invalid_preview_input_is_rejected(data):
    assert not IntakePreviewForm(data).is_valid()


def test_optional_preview_does_not_invent_mandatory_submission_rules():
    form = IntakePreviewForm({})
    assert form.is_valid()
    assert all(value == "—" for _, value in form.display_rows())


def test_zero_candidates_are_not_displayed_as_missing():
    form = IntakePreviewForm({"candidate_count": "0"})
    assert form.is_valid()
    assert any(value == 0 for _, value in form.display_rows())


def test_post_requires_csrf():
    client = Client(enforce_csrf_checks=True)
    assert client.post(reverse("intake"), {"subject": "हिन्दी"}).status_code == 403


def test_valid_same_origin_form_post_succeeds():
    client = Client(enforce_csrf_checks=True)
    page = client.get(reverse("intake"))
    assert page["Referrer-Policy"] == "same-origin"
    response = client.post(
        reverse("intake"),
        {"subject": "हिन्दी", "csrfmiddlewaretoken": client.cookies["csrftoken"].value},
        HTTP_ORIGIN="http://testserver",
    )
    assert response.status_code == 200
    assert "दर्ज विवरण की समीक्षा" in response.content.decode()


def test_health_is_not_a_database_readiness_claim(client):
    assert client.get(reverse("health")).json() == {
        "status": "ok",
        "mode": "preview",
        "persistent_storage": False,
    }


def test_invalid_policy_does_not_silently_fall_back(client):
    assert client.get(reverse("policies"), {"type": "unknown"}).status_code == 404


def test_policy_versions_are_independent_and_readonly():
    assert len({p.key for p in POLICIES.values()}) == 3
    with pytest.raises(FrozenInstanceError):
        POLICIES["principal"].professors = 6
    snapshot = POLICIES["subject_expert"].snapshot()
    snapshot["professors"] = 3
    snapshot["required_categories"].clear()
    assert POLICIES["subject_expert"].professors == 5
    assert POLICIES["principal"].professors == 5
    assert POLICIES["subject_expert"].required_categories == ("SC_ST", "OBC")


def test_only_subject_expert_policy_is_provisional():
    assert [p.appointment_type for p in POLICIES.values() if p.provisional] == ["subject_expert"]


def test_no_registration_or_allocation_mutation_routes(client):
    for route in ["/register/", "/login/", "/allocate/", "/final-lock/"]:
        assert client.get(route).status_code == 404


def test_input_not_carried_to_another_request(client):
    client.post(reverse("intake"), {"college_name": "गोपनीय नमूना"})
    assert "गोपनीय नमूना" not in client.get(reverse("intake")).content.decode()
    assert "sessionid" not in client.cookies


def test_explicit_edit_roundtrip_preserves_text_without_session(client):
    response = client.post(
        reverse("intake"),
        {"college_name": "परीक्षण महाविद्यालय", "_action": "edit"},
    )
    assert response.status_code == 200
    assert 'value="परीक्षण महाविद्यालय"' in response.content.decode()
    assert "sessionid" not in client.cookies


def test_policy_post_is_not_allowed(client):
    assert client.post(reverse("policies"), {"type": "hod"}).status_code == 405
