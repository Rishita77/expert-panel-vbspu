"""Read-only composition policies authorised in DEC-018.

This is not the pending reservation/final-selection policy. Never use the
displayed composition as permission to issue or lock an actual nomination.
"""

from dataclasses import asdict, dataclass
from types import MappingProxyType


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
            "subject-expert-v1-provisional",
            "subject_expert",
            "विषय विशेषज्ञ / प्रवक्ता",
            "Subject expert / Lecturer",
            1,
            1,
            5,
            1,
            ("SC_ST", "OBC"),
            True,
        ),
    }
)
