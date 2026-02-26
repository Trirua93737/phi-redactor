"""Fax Number recognizer for Presidio.

Detects fax numbers -- phone-format numbers that appear near fax-related
context words such as "fax", "facsimile", "fax number", "fax #".

Entity type: ``FAX_NUMBER``
"""

from __future__ import annotations

from presidio_analyzer import Pattern, PatternRecognizer


class FaxRecognizer(PatternRecognizer):
    """Detect fax numbers in clinical and administrative text.

    Fax numbers share the same format as telephone numbers but are
    distinguished by nearby context words.  HIPAA treats fax numbers
    as a separate identifier category from phone numbers.

    Patterns:
        - ``fax_us_format``: US phone format ``(XXX) XXX-XXXX`` or
          ``XXX-XXX-XXXX`` near "fax" context.  Score 0.4 (context-dependent).
        - ``fax_prefixed``: Explicit "Fax:" or "Fax #:" prefix.  Score 0.85.
    """

    PATTERNS = [
        Pattern(
            "fax_prefixed",
            r"(?i)(?:fax|facsimile)\s*(?:number|no|#|num)?[:\s#-]*"
            r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            0.85,
        ),
        Pattern(
            "fax_us_format",
            r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
            0.3,
        ),
    ]

    CONTEXT = [
        "fax",
        "facsimile",
        "fax number",
        "fax no",
        "fax #",
        "fax num",
        "telefax",
    ]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="FAX_NUMBER",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language="en",
            name="FaxRecognizer",
        )
