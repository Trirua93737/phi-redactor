"""Vehicle Identifier recognizer for Presidio.

Detects vehicle identifiers including:

- **VIN (Vehicle Identification Number)**: 17 alphanumeric characters
  excluding I, O, Q (per ISO 3779).
- **License plates**: Alphanumeric sequences near context words like
  "plate", "license plate", "tag number".

Entity type: ``VEHICLE_ID``
"""

from __future__ import annotations

from presidio_analyzer import Pattern, PatternRecognizer


class VehicleRecognizer(PatternRecognizer):
    """Detect Vehicle Identification Numbers (VIN) and license plates.

    Patterns:
        - ``vin_17char``: Exactly 17 characters from the set
          ``[A-HJ-NPR-Z0-9]`` (excludes I, O, Q per ISO 3779).
          Score 0.75 (structurally unique).
        - ``license_plate``: Common US license plate formats (1-4 letters
          + 1-4 digits or variations).  Score 0.3 (requires context).
    """

    PATTERNS = [
        Pattern(
            "vin_17char",
            r"\b[A-HJ-NPR-Z0-9]{17}\b",
            0.75,
        ),
        Pattern(
            "license_plate",
            r"\b[A-Z]{1,4}[-\s]?\d{1,4}[-\s]?[A-Z]{0,3}\b",
            0.3,
        ),
    ]

    CONTEXT = [
        "vin",
        "vehicle identification number",
        "vehicle id",
        "vehicle number",
        "license plate",
        "plate number",
        "plate #",
        "plate no",
        "tag number",
        "tag #",
        "registration plate",
        "vehicle serial",
    ]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="VEHICLE_ID",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language="en",
            name="VehicleRecognizer",
        )
