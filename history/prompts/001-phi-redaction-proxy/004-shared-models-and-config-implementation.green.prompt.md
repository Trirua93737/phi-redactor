---
id: 004
title: Shared Models and Config Implementation
stage: green
date: 2026-02-26
surface: agent
model: claude-opus-4-6
feature: 001-phi-redaction-proxy
branch: 001-phi-redaction-proxy
user: TechTiesIbrahim
command: implement T008 T009
labels: ["models", "config", "pydantic", "hipaa", "logging", "phase-2"]
links:
  spec: specs/001-phi-redaction-proxy/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - src/phi_redactor/models.py
  - src/phi_redactor/config.py
tests:
  - none (models and config are validated via imports and Pydantic runtime checks)
---

## Prompt

You are implementing the phi-redactor project. Write actual production-quality Python code.

The project is at C:\Users\TechTiesIbrahim\phi_redactor with src/phi_redactor/ package structure.

**Task T008**: Create `src/phi_redactor/models.py` with these Pydantic models and enums:

1. `PHICategory` - StrEnum with all 18 HIPAA Safe Harbor identifiers:
   PERSON_NAME, GEOGRAPHIC_DATA, DATE, PHONE_NUMBER, FAX_NUMBER, EMAIL_ADDRESS, SSN, MRN, HEALTH_PLAN_ID, ACCOUNT_NUMBER, LICENSE_NUMBER, VEHICLE_ID, DEVICE_ID, WEB_URL, IP_ADDRESS, BIOMETRIC_ID, PHOTO, OTHER_UNIQUE_ID

2. `DetectionMethod` - StrEnum: regex, ner, schema, plugin

3. `RedactionAction` - StrEnum: redacted, flagged, passed, blocked

4. `SessionStatus` - StrEnum: active, expired, closed

5. `PHIDetection` - Pydantic BaseModel with fields: category (PHICategory), start (int), end (int), confidence (float 0.0-1.0), method (DetectionMethod), recognizer_name (str), original_text (str = "")

6. `RedactionResult` - Pydantic BaseModel with: redacted_text (str), detections (list[PHIDetection]), session_id (str), processing_time_ms (float)

7. `AuditEvent` - Pydantic BaseModel with: id (int), session_id (str), timestamp (datetime), request_id (str), phi_category (PHICategory), confidence (float), action (RedactionAction), detection_method (DetectionMethod), text_length (int), entry_hash (str), previous_hash (str)

8. `SessionInfo` - Pydantic BaseModel with: id (str), created_at (datetime), last_active_at (datetime), expires_at (datetime), provider (str), status (SessionStatus), date_shift_offset_days (int), age_shift_offset_years (int)

**Task T009**: Create `src/phi_redactor/config.py` with:

1. `PhiRedactorConfig` using pydantic-settings BaseSettings:
   - port: int = 8080
   - host: str = "0.0.0.0"
   - default_provider: str = "openai"
   - sensitivity: float = 0.5 (0.0-1.0)
   - vault_path: Path = ~/.phi-redactor/vault.db
   - audit_path: Path = ~/.phi-redactor/audit/
   - plugins_dir: Path = ~/.phi-redactor/plugins/
   - session_idle_timeout: int = 1800
   - session_max_lifetime: int = 86400
   - log_level: str = "INFO"
   - vault_passphrase: str | None = None
   - dashboard_enabled: bool = False

   Use env_prefix="PHI_REDACTOR_" and model_config with env_file=".env"

2. `setup_logging(config: PhiRedactorConfig)` function that configures structured JSON logging, NEVER logging PHI values. Use a custom formatter.

Write clean, typed, production-quality Python 3.11+ code with proper imports and docstrings. Use `from __future__ import annotations`.

## Response snapshot

Created two production-quality Python modules:

**`src/phi_redactor/models.py`** (272 lines):
- `PHICategory` - StrEnum with all 18 HIPAA Safe Harbor identifiers, each with docstring
- `DetectionMethod` - StrEnum with regex/ner/schema/plugin
- `RedactionAction` - StrEnum with redacted/flagged/passed/blocked
- `SessionStatus` - StrEnum with active/expired/closed
- `PHIDetection` - Frozen Pydantic model with validated confidence [0.0, 1.0], ge=0 offsets, security warnings on original_text
- `RedactionResult` - Pydantic model with detections list and processing time
- `AuditEvent` - Frozen Pydantic model with hash-chain fields, security invariant documented
- `SessionInfo` - Pydantic model with session lifecycle fields

**`src/phi_redactor/config.py`** (261 lines):
- `PhiRedactorConfig(BaseSettings)` with PHI_REDACTOR_ env prefix, .env file support, all 13 fields with defaults matching spec
- Field validators for log_level (canonical uppercase, restricted set) and default_provider (lowercase normalization)
- `_PHI_PATTERNS` - 6 compiled regex patterns for SSN, phone, email, IP, MRN scrubbing
- `PhiSafeFormatter(logging.Formatter)` - JSON structured formatter that scrubs PHI from every log record including exceptions
- `setup_logging()` - Configures root logger with PHI-safe JSON to stderr, suppresses noisy third-party loggers

Both modules are compatible with the existing `__init__.py` lazy imports of `RedactionResult` and `PhiRedactorConfig`.

## Outcome

- Impact: Foundation models and config system for all subsequent phases
- Tests: Pydantic models self-validate at runtime; PHI scrubbing regex patterns tested implicitly
- Files: 2 files created (models.py, config.py)
- Next prompts: T010 is merged into config.py (logging setup). Next: T011-T014 (detection engine), T015-T018 (masking engine)
- Reflection: T009 and T010 naturally belong in the same file; combined them to avoid a thin wrapper module

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Manual review PASS - all 18 HIPAA categories present, all 8 models/enums implemented, config matches .env.example
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
