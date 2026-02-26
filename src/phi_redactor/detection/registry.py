"""HIPAA recognizer registry for Presidio-based PHI detection.

Registers all built-in Presidio recognizers and maps them to the 18 HIPAA
Safe Harbor identifier categories.  Custom recognizers for healthcare-specific
identifiers (MRN, health plan IDs, etc.) will be added in Phase 4 (US2).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from presidio_analyzer import PatternRecognizer, RecognizerRegistry

from phi_redactor.models import PHICategory

if TYPE_CHECKING:
    from presidio_analyzer import EntityRecognizer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mapping from Presidio entity types to our PHICategory enum
# ---------------------------------------------------------------------------

PRESIDIO_TO_PHI_CATEGORY: dict[str, PHICategory] = {
    # Built-in Presidio entity types
    "PERSON": PHICategory.PERSON_NAME,
    "LOCATION": PHICategory.GEOGRAPHIC_DATA,
    "DATE_TIME": PHICategory.DATE,
    "PHONE_NUMBER": PHICategory.PHONE_NUMBER,
    "EMAIL_ADDRESS": PHICategory.EMAIL_ADDRESS,
    "US_SSN": PHICategory.SSN,
    "URL": PHICategory.WEB_URL,
    "IP_ADDRESS": PHICategory.IP_ADDRESS,
    "US_DRIVER_LICENSE": PHICategory.LICENSE_NUMBER,
    "CREDIT_CARD": PHICategory.ACCOUNT_NUMBER,
    "US_BANK_NUMBER": PHICategory.ACCOUNT_NUMBER,
    "US_PASSPORT": PHICategory.OTHER_UNIQUE_ID,
    "US_ITIN": PHICategory.OTHER_UNIQUE_ID,
    "NRP": PHICategory.OTHER_UNIQUE_ID,
    "MEDICAL_LICENSE": PHICategory.LICENSE_NUMBER,
    # Aliases used by some Presidio versions
    "IBAN_CODE": PHICategory.ACCOUNT_NUMBER,
    "CRYPTO": PHICategory.OTHER_UNIQUE_ID,
}


class HIPAARecognizerRegistry:
    """Registers all recognizers needed for 18 HIPAA Safe Harbor identifiers.

    For the initial phase (Phase 2), this class configures Presidio's built-in
    recognizers which cover:

    - PERSON_NAME -- via spaCy NER (SpacyRecognizer)
    - PHONE_NUMBER -- built-in pattern recognizer
    - EMAIL_ADDRESS -- built-in pattern recognizer
    - SSN (US_SSN) -- built-in pattern recognizer
    - WEB_URL (URL) -- built-in pattern recognizer
    - IP_ADDRESS -- built-in pattern recognizer
    - DATE_TIME -- built-in pattern + spaCy NER
    - GEOGRAPHIC_DATA -- via spaCy NER (LOCATION entities)
    - LICENSE_NUMBER -- US_DRIVER_LICENSE built-in

    Custom healthcare-specific recognizers (MRN, health plan ID, device UDI,
    biometric, vehicle, fax, account, photo) will be added in Phase 4 (US2).
    """

    def __init__(self) -> None:
        self._recognizers: list[EntityRecognizer] = []
        self._registry = RecognizerRegistry()
        self._registry.load_predefined_recognizers()
        self._recognizers = list(self._registry.recognizers)
        logger.info(
            "Loaded %d built-in Presidio recognizers", len(self._recognizers)
        )

    @property
    def registry(self) -> RecognizerRegistry:
        """Return the underlying Presidio RecognizerRegistry."""
        return self._registry

    def get_recognizers(self) -> list[EntityRecognizer]:
        """Return list of all registered recognizer instances."""
        return list(self._recognizers)

    def get_supported_entities(self) -> list[str]:
        """Return list of all Presidio entity type strings that are supported."""
        entities: set[str] = set()
        for recognizer in self._recognizers:
            entities.update(recognizer.supported_entities)
        return sorted(entities)

    def get_supported_categories(self) -> list[PHICategory]:
        """Return list of PHICategory values that have at least one recognizer.

        Only categories that can be mapped from a registered Presidio entity
        type are included.
        """
        supported_entities = self.get_supported_entities()
        categories: set[PHICategory] = set()
        for entity in supported_entities:
            if entity in PRESIDIO_TO_PHI_CATEGORY:
                categories.add(PRESIDIO_TO_PHI_CATEGORY[entity])
        return sorted(categories, key=lambda c: c.value)

    def validate_coverage(self) -> dict[PHICategory, bool]:
        """Return dict mapping each of the 18 HIPAA categories to coverage status.

        A category is considered covered if at least one registered recognizer
        can detect the corresponding entity type.

        Returns:
            Dictionary mapping every PHICategory to a boolean indicating
            whether at least one recognizer covers it.
        """
        supported = set(self.get_supported_categories())
        return {category: category in supported for category in PHICategory}
