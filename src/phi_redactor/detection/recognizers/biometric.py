"""Biometric Identifier recognizer for Presidio.

Detects mentions of biometric identifiers via keyword context matching.
Biometric identifiers in HIPAA include fingerprints, retinal scans,
voiceprints, facial recognition data, DNA profiles, iris scans, and
palm prints.

Entity type: ``BIOMETRIC_ID``
"""

from __future__ import annotations

from presidio_analyzer import Pattern, PatternRecognizer


class BiometricRecognizer(PatternRecognizer):
    """Detect biometric identifier mentions in clinical text.

    Unlike most other recognizers, biometric identifiers are detected
    primarily through keyword matching rather than structural patterns,
    since biometric data references in text are descriptive (e.g.,
    "fingerprint on file", "retinal scan completed").

    Patterns:
        - ``biometric_keyword``: Matches specific biometric technology
          keywords.  Score 0.7 (keywords are fairly unambiguous in
          clinical context).
        - ``biometric_data_ref``: Matches references to biometric data
          storage or collection.  Score 0.6.
    """

    PATTERNS = [
        Pattern(
            "biometric_keyword",
            r"(?i)\b(?:fingerprint|finger\s*print|retinal\s*scan|retina\s*scan|"
            r"voiceprint|voice\s*print|facial\s*recognition|face\s*recognition|"
            r"iris\s*scan|palm\s*print|palm\s*scan)\b",
            0.7,
        ),
        Pattern(
            "biometric_data_ref",
            r"(?i)\b(?:dna\s*(?:profile|sample|test|analysis|sequence|marker)|"
            r"genetic\s*(?:data|profile|marker|test|information|sample|sequence)|"
            r"biometric\s*(?:data|identifier|id|sample|template|scan|record))\b",
            0.6,
        ),
    ]

    CONTEXT = [
        "fingerprint",
        "retinal scan",
        "voiceprint",
        "facial recognition",
        "dna",
        "genetic",
        "iris scan",
        "palm print",
        "biometric",
        "biometric data",
        "biometric identifier",
        "biometric id",
    ]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="BIOMETRIC_ID",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language="en",
            name="BiometricRecognizer",
        )
