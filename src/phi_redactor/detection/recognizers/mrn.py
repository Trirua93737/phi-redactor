"""Medical Record Number (MRN) recognizer for Presidio.

Detects medical record numbers -- 6-to-10 digit numeric sequences that appear
near healthcare-specific context words such as "MRN", "medical record",
"chart number", "record number", or "patient ID".

Entity type: ``MRN``
"""

from __future__ import annotations

from presidio_analyzer import Pattern, PatternRecognizer


class MRNRecognizer(PatternRecognizer):
    """Detect Medical Record Numbers (MRN).

    MRNs are typically 6-10 digit numeric identifiers assigned by a healthcare
    facility. Because bare digit sequences are ambiguous, the recognizer relies
    heavily on nearby context words to boost the confidence score.

    Patterns:
        - ``mrn_digits``: 6-10 consecutive digits (base score 0.3, boosted by context).
        - ``mrn_prefixed``: Explicit "MRN" or "MRN:" prefix followed by digits (score 0.85).
    """

    PATTERNS = [
        Pattern(
            "mrn_prefixed",
            r"(?i)\bMRN[:\s#-]*\d{6,10}\b",
            0.85,
        ),
        Pattern(
            "mrn_digits",
            r"\b\d{6,10}\b",
            0.3,
        ),
    ]

    CONTEXT = [
        "mrn",
        "medical record",
        "medical record number",
        "chart number",
        "record number",
        "patient id",
        "patient identifier",
        "hospital number",
        "encounter number",
    ]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="MRN",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language="en",
            name="MRNRecognizer",
        )
