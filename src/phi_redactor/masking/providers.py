"""Custom Faker providers for healthcare-specific identifiers.

Generates structurally valid but fictitious identifiers for medical record
numbers, health plan IDs, NPI numbers, and device UDIs.  These are registered
with a ``Faker`` instance so that ``fake.mrn()`` etc. work seamlessly within
the :class:`~phi_redactor.masking.semantic.SemanticMasker`.
"""

from __future__ import annotations

from faker.providers import BaseProvider


class HealthcareFakerProvider(BaseProvider):
    """Custom Faker provider for healthcare-specific identifiers."""

    def mrn(self) -> str:
        """Generate an 8-digit medical record number.

        Returns:
            A zero-padded string of 8 random digits, e.g. ``"00456789"``.
        """
        return self.numerify("########")

    def health_plan_id(self) -> str:
        """Generate a health plan beneficiary ID.

        Format follows common BCBS-style identifiers: ``BCBS-`` followed by
        9 random digits.

        Returns:
            A string like ``"BCBS-987654321"``.
        """
        return f"BCBS-{self.numerify('#########')}"

    def npi(self) -> str:
        """Generate a 10-digit National Provider Identifier (NPI).

        The NPI is a CMS-issued unique identifier for healthcare providers.
        Generated values are structurally valid (10 digits) but are not
        guaranteed to pass the Luhn check digit validation.

        Returns:
            A string of 10 random digits, e.g. ``"1234567890"``.
        """
        return self.numerify("##########")

    def device_udi(self) -> str:
        """Generate a UDI (Unique Device Identification) string.

        Follows the GS1 GTIN-14 format prefix ``(01)`` with 14 random digits.

        Returns:
            A string like ``"(01)00884521456781"``.
        """
        return f"(01){self.numerify('##############')}"
