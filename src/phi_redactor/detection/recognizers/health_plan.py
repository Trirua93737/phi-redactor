"""Health Plan Beneficiary ID recognizer for Presidio.

Detects health plan beneficiary numbers -- alphanumeric identifiers that appear
near insurance-related context words such as "member ID", "beneficiary",
"subscriber", "policy number", "insurance ID", or "group number".

Entity type: ``HEALTH_PLAN_ID``
"""

from __future__ import annotations

from presidio_analyzer import Pattern, PatternRecognizer


class HealthPlanRecognizer(PatternRecognizer):
    """Detect Health Plan Beneficiary IDs.

    Health plan IDs vary widely in format across insurers but are typically
    alphanumeric strings of 6-20 characters.  Detection relies on nearby
    context words to distinguish them from other alphanumeric sequences.

    Patterns:
        - ``health_plan_alpha_num``: Alphanumeric ID with optional dashes
          (e.g., "BCBS-987654321", "H12345678").  Base score 0.3, boosted
          by context.
        - ``health_plan_prefixed``: Explicit label prefix like
          "Member ID: ABC123456" (score 0.85).
    """

    PATTERNS = [
        Pattern(
            "health_plan_prefixed",
            r"(?i)(?:member\s*id|policy\s*(?:number|no|#)|group\s*(?:number|no|#)|"
            r"insurance\s*id|subscriber\s*(?:id|number|no|#)|beneficiary\s*(?:id|number|no|#))"
            r"[:\s#-]*[A-Z0-9][A-Z0-9\-]{4,19}\b",
            0.85,
        ),
        Pattern(
            "health_plan_alpha_num",
            r"\b[A-Z]{1,5}[-]?\d{6,15}\b",
            0.3,
        ),
    ]

    CONTEXT = [
        "member id",
        "member number",
        "beneficiary",
        "beneficiary id",
        "beneficiary number",
        "subscriber",
        "subscriber id",
        "subscriber number",
        "policy number",
        "policy no",
        "insurance id",
        "insurance number",
        "group number",
        "group no",
        "group id",
        "health plan",
        "health plan id",
        "plan id",
        "payer id",
        "carrier id",
    ]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="HEALTH_PLAN_ID",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language="en",
            name="HealthPlanRecognizer",
        )
