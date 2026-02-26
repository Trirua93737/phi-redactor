"""Device Identifier recognizer for Presidio.

Detects medical device identifiers including:

- **GS1 UDI**: ``(01)`` prefix followed by 14 digits (GTIN-14).
- **HIBCC UDI**: ``+`` prefix followed by alphanumeric identifier.
- **ICCBBA UDI**: ``=`` prefix followed by alphanumeric identifier.
- **Device serial numbers**: Alphanumeric sequences near context words
  like "device", "serial", "UDI".

Entity type: ``DEVICE_ID``
"""

from __future__ import annotations

from presidio_analyzer import Pattern, PatternRecognizer


class DeviceRecognizer(PatternRecognizer):
    """Detect medical device identifiers (UDI, serial numbers).

    Patterns:
        - ``udi_gs1``: GS1 format ``(01)`` + 14 digits.  Score 0.85
          (highly specific structure).
        - ``udi_hibcc``: HIBCC format ``+`` prefix + alphanumeric.
          Score 0.6 (moderately specific).
        - ``udi_iccbba``: ICCBBA format ``=`` prefix + alphanumeric.
          Score 0.6 (moderately specific).
        - ``device_serial``: Generic serial number pattern near context.
          Score 0.3 (requires context boost).
    """

    PATTERNS = [
        Pattern(
            "udi_gs1",
            r"\(01\)\d{14}",
            0.85,
        ),
        Pattern(
            "udi_hibcc",
            r"\+[A-Z0-9]{4,30}",
            0.6,
        ),
        Pattern(
            "udi_iccbba",
            r"=[A-Z0-9]{4,30}",
            0.6,
        ),
        Pattern(
            "device_serial",
            r"\b[A-Z0-9]{2,4}[-]?[A-Z0-9]{4,20}\b",
            0.2,
        ),
    ]

    CONTEXT = [
        "device",
        "device id",
        "device identifier",
        "device serial",
        "serial number",
        "serial #",
        "serial no",
        "udi",
        "unique device",
        "unique device identifier",
        "implant",
        "implant id",
        "implant serial",
        "medical device",
        "equipment id",
        "equipment serial",
    ]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="DEVICE_ID",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language="en",
            name="DeviceRecognizer",
        )
