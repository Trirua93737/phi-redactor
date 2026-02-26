---
id: 005
title: Detection Engine and Registry Implementation
stage: green
date: 2026-02-26
surface: agent
model: claude-opus-4-6
feature: 001-phi-redaction-proxy
branch: 001-phi-redaction-proxy
user: TechTiesIbrahim
command: implement T011 T012 T013 T014
labels: ["detection", "presidio", "spacy", "hipaa", "phase-2", "engine", "registry", "tests"]
links:
  spec: specs/001-phi-redaction-proxy/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - src/phi_redactor/detection/__init__.py
  - src/phi_redactor/detection/engine.py
  - src/phi_redactor/detection/registry.py
  - tests/unit/test_detection.py
tests:
  - tests/unit/test_detection.py::TestPersonNameDetection::test_detect_doctor_name
  - tests/unit/test_detection.py::TestPersonNameDetection::test_detect_patient_name
  - tests/unit/test_detection.py::TestSSNDetection::test_detect_ssn_dashed_format
  - tests/unit/test_detection.py::TestPhoneDetection::test_detect_phone_parenthesized
  - tests/unit/test_detection.py::TestEmailDetection::test_detect_email
  - tests/unit/test_detection.py::TestDateDetection::test_detect_date_written_format
  - tests/unit/test_detection.py::TestEdgeCases::test_empty_text_returns_empty_list
  - tests/unit/test_detection.py::TestEdgeCases::test_whitespace_only_returns_empty_list
  - tests/unit/test_detection.py::TestEdgeCases::test_no_phi_text
  - tests/unit/test_detection.py::TestConfidenceScores::test_confidence_in_valid_range
  - tests/unit/test_detection.py::TestConfidenceScores::test_detections_are_phi_detection_instances
  - tests/unit/test_detection.py::TestSensitivityParameter::test_higher_sensitivity_finds_more
  - tests/unit/test_detection.py::TestSensitivityParameter::test_lower_sensitivity_finds_fewer
  - tests/unit/test_detection.py::TestSensitivityParameter::test_per_call_sensitivity_override
  - tests/unit/test_detection.py::TestSensitivityParameter::test_invalid_sensitivity_raises
  - tests/unit/test_detection.py::TestDetectionOrdering::test_detections_sorted_by_position
  - tests/unit/test_detection.py::TestEngineInitialization::test_invalid_init_sensitivity_raises
---

## Prompt

You are implementing the phi-redactor project. Write actual production-quality Python code.

The project is at C:\Users\TechTiesIbrahim\phi_redactor with src/phi_redactor/ package structure.

**Task T011**: Update `src/phi_redactor/detection/__init__.py` with public exports:
```python
from phi_redactor.detection.engine import PhiDetectionEngine
__all__ = ["PhiDetectionEngine"]
```

**Task T012**: Create `src/phi_redactor/detection/engine.py` - the core detection engine:

```python
class PhiDetectionEngine:
    """PHI detection engine wrapping Microsoft Presidio with healthcare-specific recognizers."""

    def __init__(self, sensitivity: float = 0.5):
        # Initialize Presidio AnalyzerEngine with SpacyNlpEngine using en_core_web_lg
        # Register built-in recognizers via HIPAARecognizerRegistry
        # Handle spaCy model download on first use

    def detect(self, text: str, sensitivity: float | None = None) -> list[PHIDetection]:
        # Run Presidio analysis
        # Map RecognizerResult to PHIDetection model
        # Filter by confidence threshold (sensitivity: lower = more aggressive)
        # Sort by position

    def _ensure_spacy_model(self) -> None:
        # Download en_core_web_lg if not installed

    def _map_presidio_to_phi(self, result) -> PHIDetection:
        # Map Presidio entity types to PHICategory enum
```

Import PHIDetection and PHICategory from phi_redactor.models. Map Presidio entity types (PERSON, LOCATION, PHONE_NUMBER, EMAIL_ADDRESS, etc.) to our PHICategory enum. Use the confidence threshold: `threshold = 1.0 - sensitivity` (lower sensitivity = higher threshold = more aggressive redaction).

**Task T013**: Create `src/phi_redactor/detection/registry.py`:

```python
class HIPAARecognizerRegistry:
    """Registers all recognizers needed for 18 HIPAA Safe Harbor identifiers."""

    def __init__(self):
        # Built-in Presidio recognizers cover: PERSON_NAME (via spaCy), PHONE_NUMBER,
        # EMAIL_ADDRESS, SSN (US_SSN), WEB_URL (URL), IP_ADDRESS, DATE_TIME
        # Custom recognizers will be added in Phase 4 (US2)

    def get_recognizers(self) -> list:
        # Return list of all recognizer instances

    def get_supported_categories(self) -> list[PHICategory]:
        # Return list of PHICategory values that have at least one recognizer

    def validate_coverage(self) -> dict[PHICategory, bool]:
        # Return dict mapping each of 18 categories to whether it's covered
```

**Task T014**: Create `tests/unit/test_detection.py` with 17 tests across 8 test classes.

## Response snapshot

Implemented 4 files for the PHI detection engine (Tasks T011-T014):

**`src/phi_redactor/detection/__init__.py`** (16 lines):
- Public export of `PhiDetectionEngine` with `__all__`
- Module docstring with usage example

**`src/phi_redactor/detection/engine.py`** (231 lines):
- `PhiDetectionEngine` class wrapping Presidio `AnalyzerEngine`
- Initializes with `SpacyNlpEngine` using `en_core_web_lg` model
- `detect()` method with per-call sensitivity override, confidence threshold filtering (threshold = 1.0 - sensitivity), and position-based sorting
- `_ensure_spacy_model()` for automatic model download on first use
- `_map_presidio_to_phi()` mapping Presidio entity types to PHICategory enum
- `_infer_detection_method()` categorizing recognizers as NER vs REGEX
- Full type annotations, docstrings, and logging

**`src/phi_redactor/detection/registry.py`** (119 lines):
- `PRESIDIO_TO_PHI_CATEGORY` mapping dict covering 16 Presidio entity types to PHICategory values
- `HIPAARecognizerRegistry` class wrapping Presidio `RecognizerRegistry`
- `get_recognizers()`, `get_supported_entities()`, `get_supported_categories()`, `validate_coverage()` methods
- Documents which of 18 HIPAA categories are covered and which await Phase 4 custom recognizers

**`tests/unit/test_detection.py`** (370 lines):
- 17 tests in 8 test classes covering all required scenarios
- Module-level skip if spaCy model not installed (`pytestmark = pytest.mark.skipif`)
- Module-scoped fixtures for engine reuse (avoids repeated spaCy loading)
- Tests: person name (2), SSN (1), phone (1), email (1), date (1), edge cases (3), confidence scores (2), sensitivity parameter (4), ordering (1), initialization (1)

## Outcome

- Impact: Core detection engine functional with Presidio + spaCy NER for PHI identification
- Tests: 17 unit tests written covering all 8 required test scenarios plus extras
- Files: 4 files created/updated
- Next prompts: T015-T018 (masking engine), T019-T023 (vault foundation)
- Reflection: Registry cleanly separates Presidio entity mapping from engine logic; module-scoped test fixtures critical for performance with spaCy model loading

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Manual review PASS - all task requirements met
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
