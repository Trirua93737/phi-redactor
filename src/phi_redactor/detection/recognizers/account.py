"""Account Number recognizer for Presidio.

Detects account numbers -- numeric sequences of 6-12 digits that appear near
billing / account context words such as "account number", "billing",
"acct", "account #", or "acct #".

Entity type: ``ACCOUNT_NUMBER``
"""

from __future__ import annotations

from presidio_analyzer import Pattern, PatternRecognizer


class AccountRecognizer(PatternRecognizer):
    """Detect account numbers in clinical and billing text.

    Account numbers in healthcare settings (patient billing accounts,
    facility accounts) are typically 6-12 digit numeric strings.  Detection
    relies on nearby context words to avoid false positives on arbitrary
    digit sequences.

    Patterns:
        - ``account_prefixed``: Explicit label prefix like "Account #: 12345678"
          or "Acct: 12345678" (score 0.85).
        - ``account_digits``: 6-12 consecutive digits (base score 0.2, boosted
          by context).
    """

    PATTERNS = [
        Pattern(
            "account_prefixed",
            r"(?i)(?:account\s*(?:number|no|#|num)|acct\s*(?:number|no|#|num)?|"
            r"billing\s*(?:number|no|#|num|account|acct))"
            r"[:\s#-]*[A-Z]{0,4}[\-]?\d{6,12}\b",
            0.85,
        ),
        Pattern(
            "account_digits",
            r"\b\d{6,12}\b",
            0.2,
        ),
    ]

    CONTEXT = [
        "account number",
        "account no",
        "account #",
        "account num",
        "acct",
        "acct #",
        "acct number",
        "acct no",
        "billing",
        "billing number",
        "billing account",
        "billing acct",
        "patient account",
        "facility account",
    ]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="ACCOUNT_NUMBER",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language="en",
            name="AccountRecognizer",
        )
