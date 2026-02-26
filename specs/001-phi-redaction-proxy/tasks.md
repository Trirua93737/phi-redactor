# Tasks: PHI Redaction Proxy for AI/LLM Interactions

**Input**: Design documents from `/specs/001-phi-redaction-proxy/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: Tests included — this is a security-critical HIPAA compliance tool where detection accuracy is the foundation of trust.

**Organization**: Tasks grouped by user story. US1/US2/US3 are all P1 but have a natural dependency: US1 (proxy integration) requires basic detection (US2) and basic masking (US3), so foundational versions of those are in Phase 2. Story phases then enhance each capability independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1–US9)
- Exact file paths included

## Path Conventions

Single project: `src/phi_redactor/`, `tests/` at repository root (per plan.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, Python package structure, dev tooling

- [ ] T001 Create project directory structure per plan.md layout at `src/phi_redactor/` with all subpackages (`detection/`, `masking/`, `vault/`, `proxy/`, `audit/`, `cli/`, `plugins/`) and `__init__.py` files
- [ ] T002 Create `pyproject.toml` with project metadata (name=phi-redactor, python>=3.11), dependencies (fastapi, httpx, presidio-analyzer, presidio-anonymizer, spacy, faker, cryptography, click, uvicorn, pydantic), dev dependencies (pytest, pytest-asyncio, pytest-httpx, hypothesis, ruff, mypy), and `[project.scripts]` entry point `phi-redactor = "phi_redactor.cli.main:cli"`
- [ ] T003 [P] Create `ruff.toml` with Python 3.11 target, line-length 100, and `mypy.ini` for strict type checking
- [ ] T004 [P] Create `tests/conftest.py` with shared pytest fixtures (test vault, test session, sample PHI texts, mock LLM responses)
- [ ] T005 [P] Create `.env.example` with all configuration environment variables documented (PHI_REDACTOR_PORT, PHI_REDACTOR_DEFAULT_PROVIDER, PHI_REDACTOR_SENSITIVITY, PHI_REDACTOR_VAULT_PATH, PHI_REDACTOR_AUDIT_PATH)
- [ ] T006 Create `src/phi_redactor/__init__.py` with public API exports (`PhiRedactor`, `PhiDetectionEngine`, `SemanticMasker`, `PhiVault`) and `__version__`
- [ ] T007 Create `src/phi_redactor/__main__.py` for `python -m phi_redactor` entry point

**Checkpoint**: Project skeleton ready, `pip install -e .` works, pytest discovers test directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that ALL user stories depend on — shared models, config, basic detection, basic masking, vault, audit

**CRITICAL**: No user story work can begin until this phase is complete

### Shared Models & Config

- [ ] T008 Create shared Pydantic models in `src/phi_redactor/models.py`: `PHICategory` enum (18 HIPAA types), `DetectionMethod` enum (regex/ner/schema/plugin), `RedactionAction` enum (redacted/flagged/passed/blocked), `PHIDetection` dataclass (category, start, end, confidence, method, recognizer_name, original_text), `RedactionResult` (redacted_text, detections list, session_id, processing_time_ms), `SessionStatus` enum (active/expired/closed)
- [ ] T009 Create configuration system in `src/phi_redactor/config.py`: `PhiRedactorConfig` Pydantic settings model with fields for port, default_provider, sensitivity (0.0-1.0), vault_path (~/.phi-redactor/vault.db), audit_path (~/.phi-redactor/audit/), session_idle_timeout (1800), session_max_lifetime (86400), plugins_dir (~/.phi-redactor/plugins/), log_level; load from env vars (PHI_REDACTOR_*) > YAML config file > defaults
- [ ] T010 [P] Create logging setup in `src/phi_redactor/config.py`: structured JSON logging with configurable level, NEVER log PHI values (add PHI-safe formatter that redacts known patterns from log messages)

### Basic Detection Engine (Foundation for US2)

- [ ] T011 Create `src/phi_redactor/detection/__init__.py` with `PhiDetectionEngine` public export
- [ ] T012 Create `src/phi_redactor/detection/engine.py`: `PhiDetectionEngine` class wrapping Presidio `AnalyzerEngine`, initialize with `SpacyNlpEngine` using `en_core_web_lg` model, method `detect(text: str, sensitivity: float) -> list[PHIDetection]` that runs analysis and maps Presidio `RecognizerResult` to our `PHIDetection` model, handle spaCy model download on first use
- [ ] T013 Create `src/phi_redactor/detection/registry.py`: `HIPAARecognizerRegistry` that registers Presidio's built-in recognizers (SpacyRecognizer, PatternRecognizer for SSN, phone, email, URL, IP, US driver license, dates) plus placeholders for custom recognizers, method `get_supported_categories() -> list[PHICategory]`
- [ ] T014 [P] Create `tests/unit/test_detection.py`: test detection of person names, SSNs (XXX-XX-XXXX), phone numbers, email addresses, dates, URLs, and IP addresses in sample clinical text; test confidence scores are in 0.0-1.0 range; test empty text returns no detections

### Basic Masking Engine (Foundation for US3)

- [ ] T015 Create `src/phi_redactor/masking/__init__.py` with `SemanticMasker` public export
- [ ] T016 Create `src/phi_redactor/masking/semantic.py`: `SemanticMasker` class with method `mask(text: str, detections: list[PHIDetection], session_id: str) -> tuple[str, dict]` that replaces each detection with a synthetic value from Faker, returns masked text and mapping dict {original: synthetic}; basic implementation using Faker for names, SSNs, phones, emails, dates, addresses
- [ ] T017 [P] Create `src/phi_redactor/masking/providers.py`: `HealthcareFakerProvider(BaseProvider)` subclass for Faker with methods `mrn()` (8-digit numeric), `health_plan_id()`, `npi()` (10-digit), `device_udi()`; register with Faker instance
- [ ] T018 [P] Create `tests/unit/test_masking.py`: test that masked text contains no original PHI values; test that synthetic SSNs have valid format; test that synthetic names are different from originals; test that same input with same session produces same synthetic output (consistency)

### Vault Foundation

- [ ] T019 Create `src/phi_redactor/vault/__init__.py` with `PhiVault` public export
- [ ] T020 Create `src/phi_redactor/vault/encryption.py`: `VaultEncryption` class using `cryptography.fernet.Fernet` and `MultiFernet`; methods `generate_key(passphrase: str | None) -> bytes` using PBKDF2HMAC with SHA256 and 480000 iterations (auto-generate machine key if no passphrase), `encrypt(plaintext: str) -> bytes`, `decrypt(ciphertext: bytes) -> str`, `rotate_key(new_passphrase: str)`; store key in `~/.phi-redactor/vault.key`
- [ ] T021 Create `src/phi_redactor/vault/store.py`: `PhiVault` class with SQLite backend; methods `init_db()` creating tables (vault_entries, sessions), `store_mapping(session_id, original, synthetic, category) -> VaultEntry`, `lookup_by_original(session_id, original) -> str | None`, `lookup_by_synthetic(session_id, synthetic) -> str | None`, `create_session(provider, date_shift, age_shift) -> Session`, `close_session(session_id)`, `cleanup_expired()`. Original values encrypted via `VaultEncryption` before storage. Lookup by original uses SHA-256 hash index for O(1) performance.
- [ ] T022 Create `src/phi_redactor/vault/session_map.py`: `SessionTokenMap` in-memory cache backed by vault DB; methods `get_or_create_synthetic(session_id, original, category, masker) -> str` (checks cache first, then DB, then generates new), `get_original(session_id, synthetic) -> str | None` for re-hydration; thread-safe with asyncio lock
- [ ] T023 [P] Create `tests/unit/test_vault.py`: test encryption round-trip (encrypt then decrypt equals original), test vault store/lookup cycle, test session isolation (session A can't read session B), test expired session cleanup, test deduplication (same original in same session returns same synthetic)

### Audit Trail Foundation

- [ ] T024 Create `src/phi_redactor/audit/__init__.py` with `AuditTrail` public export
- [ ] T025 Create `src/phi_redactor/audit/trail.py`: `AuditTrail` class; append-only JSON Lines file writer with hash-chain integrity; methods `log_event(session_id, request_id, category, confidence, action, detection_method, text_length)` computing SHA-256 hash including previous entry's hash, `query(session_id, category, from_dt, to_dt, limit, offset) -> list[AuditEvent]`, `verify_integrity() -> bool` checking hash chain; creates audit directory on init; rotates files daily
- [ ] T026 [P] Create `tests/unit/test_audit.py`: test event logging writes to file, test hash chain integrity verification passes on valid trail, test integrity verification fails on tampered entry, test query filtering by session/category/time

**Checkpoint**: Foundation ready — detection finds PHI, masking replaces it, vault stores mappings encrypted, audit logs events. User story implementation can begin.

---

## Phase 3: User Story 1 — One-Command PHI-Safe LLM Proxy (Priority: P1) MVP

**Goal**: `pip install phi-redactor && phi-redactor serve` starts a proxy. Point OpenAI client at localhost:8080, PHI is automatically redacted outbound and re-hydrated inbound. Streaming works.

**Independent Test**: Start proxy, send clinical prompt with PHI through OpenAI SDK pointing at proxy, verify (a) upstream received no raw PHI, (b) response contains re-hydrated original values, (c) streaming mode works.

### Tests for User Story 1

- [ ] T027 [P] [US1] Create `tests/integration/test_proxy_openai.py`: test full round-trip — mock upstream OpenAI API, send request with PHI through proxy, assert upstream received masked text (no raw PHI), assert client received re-hydrated response with originals restored; test non-streaming and streaming modes
- [ ] T028 [P] [US1] Create `tests/unit/test_streaming.py`: test `StreamRehydrator` with synthetic tokens split across SSE chunks (e.g., "Sar"|"ah"| " Ch"|"en" should re-hydrate to original name); test buffer flush on stream end; test passthrough of non-PHI tokens

### Implementation for User Story 1

- [ ] T029 [US1] Create `src/phi_redactor/proxy/__init__.py` and `src/phi_redactor/proxy/app.py`: `ProxyApp` FastAPI application factory; `create_app(config: PhiRedactorConfig) -> FastAPI` initializing detection engine, masking engine, vault, audit trail, session manager, and httpx AsyncClient in lifespan handler; include CORS middleware, health endpoint at `/api/v1/health`
- [ ] T030 [US1] Create `src/phi_redactor/proxy/session.py`: `SessionManager` class; methods `get_or_create_session(request: Request) -> Session` extracting X-Session-Id header or creating new session, `cleanup_loop()` async background task running every 5 minutes to expire idle/max-lifetime sessions; stores sessions in vault
- [ ] T031 [US1] Create `src/phi_redactor/proxy/adapters/base.py`: `BaseProviderAdapter` abstract class with methods `extract_messages(request_body: dict) -> list[str]` (extracts text content from provider-specific request format), `inject_messages(request_body: dict, masked_texts: list[str]) -> dict` (replaces text content with masked versions), `parse_response_content(response_body: dict) -> str` (extracts text from response), `inject_response_content(response_body: dict, rehydrated: str) -> dict`
- [ ] T032 [US1] Create `src/phi_redactor/proxy/adapters/openai.py`: `OpenAIAdapter(BaseProviderAdapter)` implementing message extraction/injection for OpenAI chat completion format (messages[].content, system/user/assistant roles), response parsing (choices[].message.content), SSE chunk parsing (choices[].delta.content), and auth header forwarding (Authorization: Bearer)
- [ ] T033 [US1] Create `src/phi_redactor/proxy/routes/openai.py`: FastAPI route handlers for `/openai/v1/chat/completions` and `/openai/v1/embeddings` plus `/v1/chat/completions` default; request flow: parse body → extract messages → detect PHI → mask → store vault mappings → log audit events → forward to upstream via httpx → parse response → re-hydrate → return to client; handle both `stream: false` and `stream: true`
- [ ] T034 [US1] Create `src/phi_redactor/proxy/streaming.py`: `StreamRehydrator` class for SSE streaming re-hydration; sliding window buffer of configurable size (default 50 chars); build trie from session's known synthetic values on stream start; method `async process_chunk(chunk: str) -> str` that buffers tokens, checks for synthetic entity matches in buffer, emits safe prefix; method `flush() -> str` to emit remaining buffer on stream end; handles OpenAI SSE format (`data: {json}\n\n`, `data: [DONE]`)
- [ ] T035 [US1] Create `src/phi_redactor/proxy/routes/management.py`: FastAPI routes for `/api/v1/health` (version, uptime, active sessions, provider status), `/api/v1/stats` (total requests, redactions by category, avg confidence, avg latency), `/api/v1/sessions` (list/get/close sessions), `/api/v1/audit` (query audit trail with filters)
- [ ] T036 [US1] Create `src/phi_redactor/proxy/routes/library.py`: FastAPI routes for `/api/v1/redact` (POST text, get back redacted text + detections) and `/api/v1/rehydrate` (POST text + session_id, get back original text); these enable programmatic use without proxying to an LLM
- [ ] T037 [US1] Create `src/phi_redactor/cli/main.py`: Click group `cli` as entry point with `--config`, `--verbose`, `--json-output` global options
- [ ] T038 [US1] Create `src/phi_redactor/cli/serve.py`: Click command `serve` with options `--port` (default 8080), `--host` (default 0.0.0.0), `--provider` (default openai), `--sensitivity` (default 0.5); starts uvicorn with ProxyApp; prints startup banner with URL and configured provider; downloads spaCy model if not present
- [ ] T039 [US1] Wire up `PhiRedactor` facade class in `src/phi_redactor/__init__.py`: convenience class combining detection engine + masking engine + vault for library usage; methods `redact(text, session_id=None) -> RedactionResult`, `rehydrate(text, session_id) -> str`
- [ ] T040 [US1] Create `tests/integration/test_session_consistency.py`: test that same patient name across 5 sequential requests in same session always maps to same synthetic name; test that different sessions get different synthetic mappings for same original

**Checkpoint**: `phi-redactor serve` starts, OpenAI SDK works through proxy, PHI is redacted/re-hydrated including streaming. This is the MVP.

---

## Phase 4: User Story 2 — Multi-Layer PHI Detection for All 18 HIPAA Identifiers (Priority: P1)

**Goal**: Detection engine covers all 18 HIPAA Safe Harbor identifier categories with ≥95% recall. Custom recognizers fill the gaps Presidio doesn't cover.

**Independent Test**: Run detection benchmark with synthetic clinical text containing all 18 identifier types, measure precision/recall per category.

### Tests for User Story 2

- [ ] T041 [P] [US2] Create `tests/unit/test_hipaa_recognizers.py`: one test function per custom recognizer — MRN patterns (6-10 digit with context keywords), health plan IDs, account numbers, license/certificate numbers (DEA, NPI), VIN (17-char), device UDI (GS1 pattern), biometric keywords; test true positives AND false positives (non-PHI that looks similar)

### Implementation for User Story 2

- [ ] T042 [P] [US2] Create `src/phi_redactor/detection/recognizers/mrn.py`: `MRNRecognizer(PatternRecognizer)` detecting medical record number patterns (6-10 digit sequences preceded by context words like "MRN", "medical record", "chart number"); configurable format regex
- [ ] T043 [P] [US2] Create `src/phi_redactor/detection/recognizers/health_plan.py`: `HealthPlanRecognizer(PatternRecognizer)` detecting health plan beneficiary numbers with context keywords ("member ID", "beneficiary", "subscriber", "policy number")
- [ ] T044 [P] [US2] Create `src/phi_redactor/detection/recognizers/account.py`: `AccountRecognizer(PatternRecognizer)` detecting account numbers with context ("account number", "billing", "acct")
- [ ] T045 [P] [US2] Create `src/phi_redactor/detection/recognizers/license.py`: `LicenseRecognizer(PatternRecognizer)` detecting certificate/license numbers including DEA numbers (2 letters + 7 digits), NPI (10-digit with Luhn check), state license numbers with context
- [ ] T046 [P] [US2] Create `src/phi_redactor/detection/recognizers/vehicle.py`: `VehicleRecognizer(PatternRecognizer)` detecting VIN patterns (17 alphanumeric, excluding I/O/Q) and license plate patterns with context
- [ ] T047 [P] [US2] Create `src/phi_redactor/detection/recognizers/device.py`: `DeviceRecognizer(PatternRecognizer)` detecting UDI patterns (GS1 `(01)` prefix, HIBCC `+` prefix, ICCBBA `=` prefix) and device serial numbers with context
- [ ] T048 [P] [US2] Create `src/phi_redactor/detection/recognizers/biometric.py`: `BiometricRecognizer(PatternRecognizer)` detecting biometric identifier mentions via keyword context ("fingerprint", "retinal scan", "voiceprint", "facial recognition", "DNA", "genetic")
- [ ] T049 [US2] Update `src/phi_redactor/detection/registry.py`: register all 8 custom recognizers in `HIPAARecognizerRegistry`; add method `validate_coverage() -> dict[PHICategory, bool]` that verifies all 18 HIPAA categories have at least one recognizer
- [ ] T050 [US2] Create `tests/integration/test_detection_benchmark.py`: comprehensive test with a synthetic clinical document containing at least one example of each of the 18 HIPAA identifier types; assert all 18 are detected; measure and log precision/recall per category; assert overall recall ≥ 95%

**Checkpoint**: Detection engine covers all 18 HIPAA Safe Harbor categories. Run benchmark to verify recall target.

---

## Phase 5: User Story 3 — Semantic Masking with Clinically Coherent Replacements (Priority: P1)

**Goal**: Masking produces clinically coherent synthetic replacements — realistic names, shifted dates preserving temporal relationships, age-appropriate demographics, consistent identities across sessions.

**Independent Test**: Send masked clinical scenario to LLM, compare response quality against unmasked baseline; verify identity consistency across multi-turn session.

### Tests for User Story 3

- [ ] T051 [P] [US3] Create `tests/unit/test_identity_clustering.py`: test that detections for same patient (name + SSN + DOB in same sentence) are grouped into one identity cluster; test that separate patients get separate clusters
- [ ] T052 [P] [US3] Create `tests/unit/test_date_shifter.py`: test consistent date offset within session (all dates shift by same offset), test age shift preserves clinical age group (pediatric stays pediatric, geriatric stays geriatric), test temporal relationships preserved (admission date < discharge date after shift)

### Implementation for User Story 3

- [ ] T053 [US3] Create `src/phi_redactor/masking/clustering.py`: `IdentityClusterer` class with method `cluster(detections: list[PHIDetection], text: str) -> dict[str, list[PHIDetection]]` that groups related PHI tokens for the same individual using proximity analysis (tokens within same sentence/paragraph likely refer to same person) and entity co-reference (name near SSN near DOB = same patient)
- [ ] T054 [US3] Create `src/phi_redactor/masking/identity.py`: `SyntheticIdentityFactory` class; method `create_identity(cluster_id: str, session: Session) -> SyntheticIdentity` generating a complete synthetic identity package (name, DOB, SSN, MRN, phone, email, address) using Faker with locale variety; identities are deterministic per (session_id + cluster_id) for consistency; method `get_replacement(detection: PHIDetection, identity: SyntheticIdentity) -> str` returning the appropriate field from the identity
- [ ] T055 [US3] Create `src/phi_redactor/masking/date_shifter.py`: `DateShifter` class with method `shift_date(original: str, session: Session) -> str` applying session's consistent date_shift_offset_days; handles multiple date formats (MM/DD/YYYY, YYYY-MM-DD, Month DD YYYY, DD-Mon-YY); method `shift_age(original_age: int, session: Session) -> int` applying session's age_shift_offset_years capped at ±5 to preserve clinical age group
- [ ] T056 [US3] Update `src/phi_redactor/masking/semantic.py`: refactor `SemanticMasker` to use `IdentityClusterer` for grouping, `SyntheticIdentityFactory` for coherent identities, `DateShifter` for temporal values; ensure mask/unmask round-trip consistency via vault
- [ ] T057 [US3] Create `tests/integration/test_masking_quality.py`: test that masked clinical note "John Smith, 67M, HbA1c 9.2%, metformin 1000mg BID" produces replacement with (a) different realistic name, (b) age in similar clinical range, (c) preserved clinical details (HbA1c, metformin); test multi-turn consistency across 5 requests

**Checkpoint**: Masking produces clinically coherent replacements. Combined with Phase 3 (proxy) and Phase 4 (detection), the full P1 MVP is complete.

---

## Phase 6: User Story 4 — Vault-Based Tokenization with Encrypted Storage (Priority: P2)

**Goal**: Vault provides encrypted at-rest storage with key rotation, session isolation, automatic expiration, and export of anonymized audit data.

**Independent Test**: Verify vault file is unreadable without key, key rotation works, expired sessions are cleaned up, concurrent sessions are isolated.

### Tests for User Story 4

- [ ] T058 [P] [US4] Create `tests/unit/test_vault_encryption.py`: test that raw vault SQLite file contains no plaintext PHI (grep for known test values), test key rotation via MultiFernet (old entries still decryptable after rotation), test PBKDF2 key derivation produces consistent keys from same passphrase

### Implementation for User Story 4

- [ ] T059 [US4] Enhance `src/phi_redactor/vault/encryption.py`: add `MultiFernet` key rotation — `rotate_key(new_passphrase)` generates new Fernet key, creates MultiFernet with [new_key, old_key], re-encrypts active session entries; add `VaultKeyManager` that stores key metadata (created_at, rotation_count) alongside vault.key
- [ ] T060 [US4] Enhance `src/phi_redactor/vault/store.py`: add `export_anonymized(session_id) -> dict` returning session statistics (redaction counts by category, date range, total entries) without any PHI; add `purge_session(session_id)` for secure deletion (overwrite then delete); add `get_vault_stats() -> dict` returning total sessions, total entries, disk size
- [ ] T061 [US4] Create `src/phi_redactor/cli/sessions.py`: Click commands `sessions list` (show active/expired sessions with counts), `sessions inspect <id>` (show session details and anonymized stats), `sessions close <id>` (close and optionally purge), `sessions cleanup` (remove all expired sessions)
- [ ] T062 [US4] Create `tests/integration/test_vault_isolation.py`: test two concurrent sessions processing same PHI get different synthetic mappings, test session A cannot lookup session B's entries, test expired session entries are unrecoverable after cleanup

**Checkpoint**: Vault provides full encrypted storage lifecycle. Sessions are isolated, keys rotate, expiration works.

---

## Phase 7: User Story 5 — Compliance-as-Code Audit Trail and Reporting (Priority: P2)

**Goal**: Generate HIPAA Safe Harbor compliance evidence reports from audit data. Audit trail is tamper-evident. Reports are auditor-ready.

**Independent Test**: Process batch of redactions, generate Safe Harbor report, verify it contains all required sections and no PHI.

### Tests for User Story 5

- [ ] T063 [P] [US5] Create `tests/integration/test_compliance.py`: test that generated Safe Harbor report contains methodology section, all 18 HIPAA categories listed, accuracy metrics, sample anonymized logs; test report contains ZERO original PHI values (grep for test values); test hash chain verification passes on generated report data

### Implementation for User Story 5

- [ ] T064 [US5] Create `src/phi_redactor/audit/reports.py`: `ComplianceReportGenerator` class; method `generate_safe_harbor(from_dt, to_dt, format) -> ComplianceReport` producing HIPAA Safe Harbor attestation document with sections: Executive Summary, De-Identification Methodology (Safe Harbor method description), Identifier Coverage (table of all 18 categories with detection status and count), Detection Accuracy Metrics (confidence distribution, recall estimates), Session Summary (anonymized), Sample Audit Log Entries (anonymized), Attestation Statement
- [ ] T065 [US5] Add Markdown report renderer in `src/phi_redactor/audit/reports.py`: `render_markdown(report: ComplianceReport) -> str` producing well-formatted Markdown with tables and sections
- [ ] T066 [US5] Add HTML report renderer in `src/phi_redactor/audit/reports.py`: `render_html(report: ComplianceReport) -> str` producing standalone HTML with inline CSS for professional appearance (printable/PDF-able via browser)
- [ ] T067 [US5] Create `src/phi_redactor/cli/report.py`: Click commands `report safe-harbor --from <date> --to <date> --format <md|html>` generating compliance report to file, `report audit-summary` for quick session-level summary
- [ ] T068 [US5] Wire compliance report endpoint in `src/phi_redactor/proxy/routes/management.py`: POST `/api/v1/reports/safe-harbor` generates report and returns report_id + output_path

**Checkpoint**: Compliance reports are generated from audit data. Auditor-ready Safe Harbor evidence package available via CLI and API.

---

## Phase 8: User Story 6 — Multi-Provider Drop-In Proxy Support (Priority: P2)

**Goal**: Proxy works transparently as drop-in for Anthropic, Google Vertex AI, and Azure OpenAI in addition to OpenAI.

**Independent Test**: Send same clinical prompt through proxy targeting each provider, verify PHI redaction/re-hydration works identically.

### Tests for User Story 6

- [ ] T069 [P] [US6] Create `tests/integration/test_proxy_anthropic.py`: test full round-trip with mock Anthropic API — verify request format translation (x-api-key header, anthropic-version, system as top-level field), SSE named events (message_start, content_block_delta, message_stop), and PHI redaction/re-hydration
- [ ] T070 [P] [US6] Create `tests/contract/test_anthropic_contract.py`: test that proxy correctly translates OpenAI-format requests to Anthropic format if auto-detect is used, test that direct Anthropic-format requests pass through correctly

### Implementation for User Story 6

- [ ] T071 [US6] Create `src/phi_redactor/proxy/adapters/anthropic.py`: `AnthropicAdapter(BaseProviderAdapter)` implementing message extraction/injection for Anthropic format (system as top-level field, content[] typed blocks), response parsing (content[].text), SSE parsing (named events: message_start → content_block_delta with delta.text → message_stop), auth header mapping (x-api-key + anthropic-version)
- [ ] T072 [US6] Create `src/phi_redactor/proxy/routes/anthropic.py`: FastAPI route handler for `/anthropic/v1/messages`; same redaction flow as OpenAI routes but using AnthropicAdapter for format translation; handle streaming with Anthropic's named SSE event format
- [ ] T073 [US6] Update `src/phi_redactor/proxy/streaming.py`: add `AnthropicStreamRehydrator` handling Anthropic's named SSE events (extract text from content_block_delta events, re-hydrate, reconstruct event format); share trie-based matching logic with OpenAI rehydrator via base class
- [ ] T074 [US6] Update `src/phi_redactor/proxy/app.py`: register Anthropic routes, add provider configuration (base URLs, auth patterns) from ProviderEndpoint model; add `/v1/messages` route that auto-detects Anthropic format
- [ ] T075 [US6] Create `src/phi_redactor/cli/config.py`: Click command `config show` displaying current config, `config set <key> <value>` for persistent configuration, `config providers` listing configured providers with status

**Checkpoint**: Proxy works with both OpenAI and Anthropic. Developers switch providers by changing base_url only.

---

## Phase 9: User Story 7 — FHIR-Native Healthcare Data Understanding (Priority: P3)

**Goal**: System natively understands FHIR JSON resources, HL7v2 messages, and CDA XML documents, using schema-aware redaction instead of generic pattern matching.

**Independent Test**: Pass FHIR Patient resource, HL7v2 ADT message, and mixed prompt through detection; verify PHI fields are identified by schema position, not just pattern matching.

### Tests for User Story 7

- [ ] T076 [P] [US7] Create `tests/unit/test_fhir_recognizer.py`: test FHIR Patient resource — name, birthDate, address, identifier fields detected as PHI; resourceType, active, code fields NOT detected; test FHIR Encounter and Observation resources
- [ ] T077 [P] [US7] Create `tests/unit/test_hl7v2_recognizer.py`: test HL7v2 ADT message — PID.5 (patient name), PID.7 (DOB), PID.19 (SSN) detected; MSH (message header) fields NOT detected

### Implementation for User Story 7

- [ ] T078 [US7] Create `src/phi_redactor/detection/recognizers/fhir.py`: `FHIRResourceRecognizer(EntityRecognizer)` that detects FHIR JSON resources by `resourceType` field, applies PHI field mapping per FHIR spec (Patient: name, birthDate, address, telecom, identifier; Encounter: subject, participant; Observation: subject, performer); returns PHIDetection with detection_method=schema and specific HIPAA category per field
- [ ] T079 [US7] Create `src/phi_redactor/detection/hl7.py`: `HL7v2Recognizer(EntityRecognizer)` parsing HL7v2 pipe-delimited messages; identifies PHI by segment/field position (PID.3=MRN, PID.5=Name, PID.7=DOB, PID.8=Sex, PID.11=Address, PID.13=Phone, PID.19=SSN; NK1.2=Name, NK1.4=Address, NK1.5=Phone); returns PHIDetection with segment position info
- [ ] T080 [US7] Update `src/phi_redactor/detection/registry.py`: register FHIRResourceRecognizer and HL7v2Recognizer; update `validate_coverage()` to include schema-based detection

**Checkpoint**: FHIR and HL7v2 content in prompts is detected with schema-aware precision, reducing false positives vs. generic pattern matching.

---

## Phase 10: User Story 8 — Plugin Architecture for Custom Redaction Rules (Priority: P3)

**Goal**: Organizations can extend detection and masking with custom Python plugin modules.

**Independent Test**: Create sample plugin with custom recognizer, load it, verify it integrates with detection pipeline.

### Tests for User Story 8

- [ ] T081 [P] [US8] Create `tests/unit/test_plugins.py`: test plugin discovery from directory, test plugin loading registers recognizer with engine, test plugin error isolation (broken plugin doesn't crash system), test plugin disable/enable

### Implementation for User Story 8

- [ ] T082 [US8] Create `src/phi_redactor/plugins/loader.py`: `PluginLoader` class; scans configured plugins directory for Python modules; each module must expose `register_recognizers(registry)` and/or `register_maskers(masker)` functions; loads via `importlib.import_module`; wraps each load in try/except for isolation; tracks loaded plugins with metadata (name, version, recognizers, load_error)
- [ ] T083 [US8] Create `src/phi_redactor/plugins/__init__.py`: public `PluginManager` class wrapping PluginLoader with methods `load_all()`, `list_plugins() -> list[PluginInfo]`, `enable(name)`, `disable(name)`, `reload(name)`
- [ ] T084 [US8] Create sample plugin at `examples/plugins/custom_mrn_plugin.py`: demonstrates how to create a custom recognizer for a hospital-specific MRN format "HOSP-XXXX-YYYY" with context keyword detection; includes docstring with plugin API documentation
- [ ] T085 [US8] Create `src/phi_redactor/cli/plugins.py`: Click commands `plugins list` (show loaded plugins with status), `plugins reload` (reload all plugins), `plugins validate <path>` (check if a plugin module is valid)
- [ ] T086 [US8] Wire plugin loading into `src/phi_redactor/detection/engine.py`: `PhiDetectionEngine.__init__` calls `PluginManager.load_all()` and registers plugin recognizers after built-in recognizers

**Checkpoint**: Plugin system works. Custom recognizers can be dropped into plugins directory and auto-loaded.

---

## Phase 11: User Story 9 — Web Dashboard for Monitoring and Compliance Posture (Priority: P3)

**Goal**: Lightweight web dashboard showing real-time proxy statistics, audit trail, and compliance posture.

**Independent Test**: Start dashboard, process requests through proxy, verify dashboard shows updated statistics within 2 seconds.

### Implementation for User Story 9

- [ ] T087 [US9] Create `src/phi_redactor/dashboard/` package with `__init__.py`
- [ ] T088 [US9] Create `src/phi_redactor/dashboard/static/index.html`: single-page dashboard with sections for: overview stats (total requests, total redactions, active sessions, uptime), redactions by category (bar chart), confidence distribution (histogram), recent audit events (table with filters), session list; uses vanilla JS + fetch API to poll `/api/v1/stats` and `/api/v1/audit` endpoints every 2 seconds; minimal CSS for clean professional appearance; no build step required
- [ ] T089 [US9] Create `src/phi_redactor/dashboard/routes.py`: FastAPI route to serve static dashboard files at `/dashboard`; WebSocket endpoint `/ws/stats` pushing real-time updates as alternative to polling
- [ ] T090 [US9] Update `src/phi_redactor/proxy/app.py`: mount dashboard routes when `--dashboard` flag is passed; dashboard is optional and adds no overhead when disabled
- [ ] T091 [US9] Create `src/phi_redactor/cli/serve.py`: add `--dashboard` flag to serve command; when enabled, prints dashboard URL alongside proxy URL on startup

**Checkpoint**: Dashboard provides real-time visibility. Useful for demos and compliance monitoring.

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Production readiness, documentation, packaging, security hardening

- [ ] T092 [P] Create `README.md` at repository root: project description, badges (PyPI, license, Python version, HIPAA), architecture diagram (text-based), installation instructions, quickstart code examples (OpenAI, Anthropic, library), CLI reference, configuration guide, compliance section, contributing guide, license (Apache-2.0)
- [ ] T093 [P] Create `LICENSE` file with Apache-2.0 license text
- [ ] T094 [P] Create `.github/workflows/ci.yml`: GitHub Actions CI running pytest, ruff lint, mypy type check on Python 3.11/3.12/3.13 matrix, with spaCy model download cached
- [ ] T095 Finalize `pyproject.toml` for PyPI publishing: classifiers (Development Status, Framework, Intended Audience :: Healthcare Industry, Topic :: Security, License :: OSI Approved :: Apache), project-urls (Homepage, Documentation, Repository, Issues), long_description from README
- [ ] T096 Create `src/phi_redactor/py.typed` marker file for PEP 561 type stub support
- [ ] T097 Security hardening review: verify no PHI in any log output, verify vault encryption is applied to all stored originals, verify audit trail never contains raw PHI, verify error responses don't leak PHI, verify streaming buffer is cleared on errors
- [ ] T098 Performance validation: benchmark redaction latency on realistic clinical notes (target <100ms p95), benchmark vault lookup latency (target <1ms), benchmark proxy overhead vs. direct API call
- [ ] T099 Run quickstart.md validation: execute all code examples from quickstart.md end-to-end against real (or mock) LLM APIs to verify documentation accuracy
- [ ] T100 Create `SECURITY.md` with vulnerability reporting instructions, security design overview, and HIPAA compliance statement

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **User Stories (Phase 3–11)**: All depend on Phase 2 completion
  - **US1 (Phase 3)**: Can start after Phase 2
  - **US2 (Phase 4)**: Can start after Phase 2 (parallel with US1 if staffed)
  - **US3 (Phase 5)**: Can start after Phase 2 (parallel with US1/US2 if staffed)
  - **US4 (Phase 6)**: Can start after Phase 2 (enhances vault from Phase 2)
  - **US5 (Phase 7)**: Can start after Phase 2 (enhances audit from Phase 2)
  - **US6 (Phase 8)**: Depends on US1 (proxy must exist to add providers)
  - **US7 (Phase 9)**: Can start after Phase 2 (adds recognizers independently)
  - **US8 (Phase 10)**: Can start after Phase 2 (adds plugin system independently)
  - **US9 (Phase 11)**: Depends on US1 (dashboard consumes management API)
- **Polish (Phase 12)**: Depends on US1–US3 minimum (core P1 stories)

### User Story Dependencies

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundation)
    │
    ├──▶ Phase 3 (US1: Proxy) ──────────▶ Phase 8 (US6: Multi-Provider)
    │                                      Phase 11 (US9: Dashboard)
    ├──▶ Phase 4 (US2: Detection) ──────┐
    │                                    ├──▶ Phase 12 (Polish)
    ├──▶ Phase 5 (US3: Masking) ────────┘
    │
    ├──▶ Phase 6 (US4: Vault)
    ├──▶ Phase 7 (US5: Compliance)
    ├──▶ Phase 9 (US7: FHIR)
    └──▶ Phase 10 (US8: Plugins)
```

### Within Each User Story

- Tests written FIRST (fail before implementation)
- Models/data structures before services
- Core logic before integration
- Verify checkpoint before moving to next phase

### Parallel Opportunities

**Phase 1**: T003, T004, T005 can all run in parallel
**Phase 2**: T010, T014, T017, T018, T023, T026 can run in parallel (different files)
**Phase 3**: T027, T028 tests in parallel; then implementation sequentially
**Phase 4**: T042–T048 (all 7 custom recognizers) can ALL run in parallel — each is a separate file
**Phase 5**: T051, T052 tests in parallel; T053, T054, T055 partially parallel
**Phase 6–11**: Independent phases can run in parallel if team capacity allows

---

## Parallel Example: User Story 2 (Detection)

```bash
# All 7 custom recognizers can be implemented simultaneously:
Task: "T042 MRN recognizer in src/phi_redactor/detection/recognizers/mrn.py"
Task: "T043 Health plan recognizer in src/phi_redactor/detection/recognizers/health_plan.py"
Task: "T044 Account recognizer in src/phi_redactor/detection/recognizers/account.py"
Task: "T045 License recognizer in src/phi_redactor/detection/recognizers/license.py"
Task: "T046 Vehicle recognizer in src/phi_redactor/detection/recognizers/vehicle.py"
Task: "T047 Device recognizer in src/phi_redactor/detection/recognizers/device.py"
Task: "T048 Biometric recognizer in src/phi_redactor/detection/recognizers/biometric.py"
```

---

## Implementation Strategy

### MVP First (Phases 1–3 = US1 Only)

1. Complete Phase 1: Setup (T001–T007)
2. Complete Phase 2: Foundational (T008–T026)
3. Complete Phase 3: User Story 1 — Proxy (T027–T040)
4. **STOP and VALIDATE**: `phi-redactor serve` works, OpenAI SDK proxied, PHI redacted
5. This alone is demoable and valuable

### P1 Complete (Phases 1–5 = US1 + US2 + US3)

1. MVP above
2. Phase 4: Full 18-identifier detection (T041–T050)
3. Phase 5: Clinically coherent semantic masking (T051–T057)
4. **VALIDATE**: Full P1 feature set — this is launch-ready for GitHub

### Full Product (All Phases)

1. P1 complete above
2. Phase 6–8: P2 stories (vault hardening, compliance reports, multi-provider)
3. Phase 9–11: P3 stories (FHIR, plugins, dashboard)
4. Phase 12: Polish, packaging, README, CI

---

## Summary

| Metric | Count |
|--------|-------|
| **Total Tasks** | 100 |
| **Phase 1 (Setup)** | 7 |
| **Phase 2 (Foundation)** | 19 |
| **Phase 3 (US1: Proxy)** | 14 |
| **Phase 4 (US2: Detection)** | 10 |
| **Phase 5 (US3: Masking)** | 7 |
| **Phase 6 (US4: Vault)** | 5 |
| **Phase 7 (US5: Compliance)** | 6 |
| **Phase 8 (US6: Multi-Provider)** | 7 |
| **Phase 9 (US7: FHIR)** | 5 |
| **Phase 10 (US8: Plugins)** | 6 |
| **Phase 11 (US9: Dashboard)** | 5 |
| **Phase 12 (Polish)** | 9 |
| **Parallel opportunities** | 40+ tasks marked [P] |
| **MVP scope** | Phases 1–3 (40 tasks) |
| **Suggested launch scope** | Phases 1–5 (57 tasks, all P1 stories) |

## Notes

- [P] tasks = different files, no dependencies on in-progress tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Tests are written first and must fail before implementation
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- spaCy model download (~560MB) happens once on first run — cache in CI
