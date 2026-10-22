"""Read-only composition policies authorised in DEC-018.

This is not the pending reservation/final-selection policy. Never use the
displayed composition as permission to issue or lock an actual nomination.
"""

from dataclasses import asdict, dataclass
from types import MappingProxyType
from django.utils.translation import gettext_noop


# Dynamic policy labels are also exposed to gettext extraction. Stored policy
# snapshots continue to contain the original Hindi and English facts.
TRANSLATABLE_POLICY_LABELS = (
    gettext_noop("प्राचार्य"),
    gettext_noop("विभागाध्यक्ष"),
    gettext_noop("विषय विशेषज्ञ / प्रवक्ता"),
)


@dataclass(frozen=True)
class CompositionPolicy:
    key: str
    appointment_type: str
    label_hi: str
    label_en: str
    version: int
    principals: int
    professors: int
    vc_nominees: int
    required_categories: tuple[str, ...]
    provisional: bool
    principal_from_requesting_college: bool = False
    final_professors: int = 4

    def snapshot(self) -> dict:
        # Return an independent structure: callers cannot mutate the policy.
        result = asdict(self)
        result["required_categories"] = list(self.required_categories)
        return result


POLICIES = MappingProxyType(
    {
        "principal": CompositionPolicy(
            "principal-v1",
            "principal",
            "प्राचार्य",
            "Principal",
            1,
            1,
            5,
            1,
            ("SC_ST", "OBC"),
            False,
        ),
        "hod": CompositionPolicy(
            "hod-v1",
            "hod",
            "विभागाध्यक्ष",
            "Head of Department",
            1,
            1,
            5,
            1,
            ("SC_ST", "OBC"),
            False,
        ),
        "subject_expert": CompositionPolicy(
            "subject-expert-v2",
            "subject_expert",
            "विषय विशेषज्ञ / प्रवक्ता",
            "Subject expert / Lecturer",
            2,
            1,
            5,
            2,
            ("SC_ST", "OBC"),
            False,
            True,
        ),
    }
)
