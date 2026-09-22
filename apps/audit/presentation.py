from apps.accounts.models import Role

LABELS = {
    "username": "लॉगिन नाम",
    "full_name": "पूरा नाम",
    "email": "ईमेल",
    "is_active": "सक्रिय",
    "roles": "अनुमतियाँ",
    "name": "नाम",
    "official_code": "आधिकारिक कोड",
    "district": "जनपद",
    "address": "पता",
    "institution_kind": "संस्था का प्रकार",
    "management_type": "प्रबन्धन प्रकार",
    "is_affiliated_to_vbspu": "VBSPU से सम्बद्ध",
    "affiliation_details": "सम्बद्धता विवरण",
    "is_requesting_college": "अनुरोध महाविद्यालय",
    "institution_name": "महाविद्यालय",
    "subject_name": "विषय",
    "appointment_type": "नियुक्ति का पद",
    "contact_details": "प्राचार्य / प्रबन्धक का विवरण",
    "vacancy": "रिक्ति का स्वरूप",
    "sanctioned_post": "स्वीकृत पद",
    "advertisement": "विज्ञापन सन्दर्भ",
    "selection_date": "प्रस्तावित चयन तिथि",
    "candidate_count": "अभ्यर्थियों की संख्या",
    "remarks": "टिप्पणी",
    "revision": "संशोधन",
    "must_change_password": "पासवर्ड परिवर्तन आवश्यक",
    "temporary_password_expires_at": "अस्थायी पासवर्ड की समय-सीमा",
    "password_changed_at": "पासवर्ड परिवर्तन समय",
}
ACTIONS = {
    "created": "नया रिकॉर्ड",
    "updated": "रिकॉर्ड में बदलाव",
    "login": "साइन इन",
    "logout": "साइन आउट",
    "local_password_setup": "स्थानीय खाता सेटअप",
    "credentials_issued": "प्रमाण-पत्र जारी / रीसेट",
    "password_changed": "पासवर्ड बदला",
    "otp_issued": "ईमेल सत्यापन कोड भेजा",
    "otp_verified": "ईमेल सत्यापन सफल",
    "otp_failed": "ईमेल सत्यापन असफल",
    "otp_delivery_failed": "ईमेल सत्यापन कोड नहीं भेजा जा सका",
    "otp_resend_limited": "ईमेल कोड पुनः भेजने की सीमा",
    "review_accepted": "प्रारूप समीक्षा स्वीकृत",
}
VALUES = {
    "principal": "प्राचार्य",
    "hod": "विभागाध्यक्ष",
    "subject_expert": "विषय विशेषज्ञ",
    "college": "महाविद्यालय",
    "university": "विश्वविद्यालय",
    "government": "राजकीय",
    "aided": "अनुदानित",
    "other": "अन्य",
    "unknown": "अज्ञात",
}


def display_rows(values):
    rows = []
    for key, value in values.items():
        if key in {"institution_id", "subject_id"}:
            continue
        if key == "roles":
            value = ", ".join(str(Role(item).label) for item in value)
        elif isinstance(value, bool):
            value = "हाँ" if value else "नहीं"
        elif key in {"appointment_type", "institution_kind", "management_type"}:
            value = VALUES.get(value, value)
        rows.append((LABELS.get(key, key), "—" if value is None or value == "" else value))
    return rows


def present(event):
    event.action_label = ACTIONS.get(event.action.rsplit(".", 1)[-1], "परिवर्तन")
    event.before_rows = display_rows(event.before)
    event.after_rows = display_rows(event.after)
    return event
