# Implementation Plan: PHI Redaction Proxy for AI/LLM Interactions

**Branch**: `001-phi-redaction-proxy` | **Date**: 2026-02-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-phi-redaction-proxy/spec.md`

## Summary

Build an open-source Python CLI tool and library (`phi-redactor`) that operates as a transparent reverse proxy between AI applications and LLM APIs. The system intercepts outgoing requests, detects PHI using a hybrid engine (Presidio + spaCy NER + custom healthcare recognizers covering all 18 HIPAA Safe Harbor identifiers), replaces PHI with clinically coherent synthetic values via Faker-based semantic masking, forwards sanitized requests to the upstream LLM, re-hydrates synthetic tokens in responses (including streaming SSE), and logs everything in a tamper-evident audit trail. All PHI mappings are stored in a local Fernet-encrypted SQLite vault that never leaves the machine.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI 0.110+, httpx 0.27+, presidio-analyzer 2.2+, presidio-anonymizer 2.2+, spaCy 3.7+ (en_core_web_lg), Faker 40+, cryptography 42+, Click 8.1+, uvicorn 0.29+, pydantic 2.6+
**Storage**: SQLite 3.35+ (local, Fernet-encrypted vault entries) + append-only JSON Lines (audit trail)
**Testing**: pytest 8+ with pytest-asyncio, pytest-httpx for proxy testing, hypothesis for property-based testing
**Target Platform**: Cross-platform (Linux, macOS, Windows) — Python-only dependencies, no native compilation
**Project Type**: Single project — Python package with CLI + library + embedded server
**Performance Goals**: <100ms p95 redaction latency per request, 50+ concurrent sessions, sub-1ms vault lookups
**Constraints**: Zero PHI leakage to external services (fail-safe: block rather than leak), installable via `pip install` in <60 seconds, no cloud dependencies
**Scale/Scope**: Single-developer to small-team workstation use; not multi-tenant server

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution is currently a template (unfilled). The following principles are adopted for this project based on project context:

| Principle | Status | Notes |
|-----------|--------|-------|
| Library-First | PASS | Core detection, masking, vault, and audit are standalone libraries; proxy is a thin wrapper |
| CLI Interface | PASS | Click-based CLI exposes all functionality; supports JSON + human-readable output |
| Test-First | PASS | pytest with contract, integration, and unit test tiers |
| Security-First | PASS | Fernet encryption at rest, fail-safe blocking, zero PHI in logs/audit |
| Simplicity | PASS | Single `pip install`, one-command startup, no external service dependencies |
| Observability | PASS | Structured audit trail, compliance reports, health endpoint, optional dashboard |

**Pre-Phase 0 Gate**: PASS
**Post-Phase 1 Gate**: PASS — design maintains all principles. No constitution violations.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        phi-redactor                                 │
│                                                                     │
│  ┌──────────┐    ┌───────────────────────────────────────────────┐  │
│  │   CLI    │    │              Proxy Server (FastAPI)            │  │
│  │  (Click) │    │                                               │  │
│  └────┬─────┘    │  /openai/v1/*  → OpenAI adapter               │  │
│       │          │  /anthropic/v1/* → Anthropic adapter           │  │
│       │          │  /v1/*          → Default provider             │  │
│       ▼          │  /api/v1/*      → Management & Library API    │  │
│  ┌──────────┐    └───────┬───────────────────────┬───────────────┘  │
│  │ Library  │            │                       │                  │
│  │   API    │◄───────────┘                       │                  │
│  │          │                                    │                  │
│  └────┬─────┘                                    │                  │
│       │                                          │                  │
│       ▼                                          ▼                  │
│  ┌───────────────────┐    ┌─────────────────────────────────────┐  │
│  │  Detection Engine │    │         Provider Adapters            │  │
│  │                   │    │                                     │  │
│  │  ┌─────────────┐  │    │  ┌─────────┐  ┌──────────┐         │  │
│  │  │  Presidio    │  │    │  │ OpenAI  │  │Anthropic │  ...    │  │
│  │  │  Analyzer    │  │    │  │ Adapter │  │ Adapter  │         │  │
│  │  │             │  │    │  └────┬────┘  └────┬─────┘         │  │
│  │  │ ┌─────────┐ │  │    │       │            │               │  │
│  │  │ │ spaCy   │ │  │    │       ▼            ▼               │  │
│  │  │ │ NER     │ │  │    │     httpx AsyncClient              │  │
│  │  │ └─────────┘ │  │    │       │                            │  │
│  │  │ ┌─────────┐ │  │    └───────┼────────────────────────────┘  │
│  │  │ │ Regex   │ │  │            │                               │
│  │  │ │Recogn.  │ │  │            ▼                               │
│  │  │ └─────────┘ │  │    ┌──────────────┐                       │
│  │  │ ┌─────────┐ │  │    │ Upstream LLM │                       │
│  │  │ │ Custom  │ │  │    │   API        │                       │
│  │  │ │HealthRe │ │  │    └──────────────┘                       │
│  │  │ └─────────┘ │  │                                           │
│  │  │ ┌─────────┐ │  │                                           │
│  │  │ │ Plugins │ │  │                                           │
│  │  │ └─────────┘ │  │                                           │
│  │  └─────────────┘  │                                           │
│  └────────┬──────────┘                                           │
│           │                                                      │
│           ▼                                                      │
│  ┌───────────────────┐    ┌──────────────────────────────────┐   │
│  │  Masking Engine   │    │         Audit Trail              │   │
│  │                   │    │                                  │   │
│  │  ┌─────────────┐  │    │  ┌────────────────────────────┐  │   │
│  │  │Faker-based  │  │    │  │ Hash-chain append-only log │  │   │
│  │  │Semantic     │  │    │  │ (JSON Lines)               │  │   │
│  │  │Replacement  │  │    │  └────────────────────────────┘  │   │
│  │  └─────────────┘  │    │  ┌────────────────────────────┐  │   │
│  └────────┬──────────┘    │  │ Compliance Report Generator│  │   │
│           │               │  │ (MD / HTML / PDF)          │  │   │
│           ▼               │  └────────────────────────────┘  │   │
│  ┌───────────────────┐    └──────────────────────────────────┘   │
│  │    Vault          │                                           │
│  │  (SQLite +        │                                           │
│  │   Fernet)         │                                           │
│  └───────────────────┘                                           │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Design

### C1: Detection Engine (`phi_redactor.detection`)

**Responsibility**: Detect all 18 HIPAA Safe Harbor identifiers in text with ≥95% recall.

**Design**:
- Wraps Presidio `AnalyzerEngine` with a custom `RecognizerRegistry` containing built-in + 8 custom healthcare recognizers
- spaCy `en_core_web_lg` as the NLP backend for NER (person names, locations, organizations)
- Regex-based recognizers for structured identifiers (SSN, phone, email, MRN, etc.)
- Plugin-loaded recognizers for extensibility
- Returns list of `PHIDetection` objects with category, span, confidence, method

**Key classes**:
- `PhiDetectionEngine` — orchestrator, wraps Presidio AnalyzerEngine
- `HIPAARecognizerRegistry` — registers all 18 HIPAA recognizers
- `MRNRecognizer`, `HealthPlanRecognizer`, `DeviceIdRecognizer`, etc. — custom recognizers
- `FHIRResourceRecognizer` — schema-aware FHIR JSON PHI detection
- `HL7v2Recognizer` — segment-aware HL7v2 message PHI detection

### C2: Masking Engine (`phi_redactor.masking`)

**Responsibility**: Replace detected PHI with clinically coherent synthetic values.

**Design**:
- `SemanticMasker` generates synthetic replacements using Faker with healthcare extensions
- `IdentityClusterer` groups related PHI tokens for the same individual (e.g., links a name + SSN + DOB as one patient)
- `DateShifter` applies consistent temporal offset per session
- `SyntheticIdentityFactory` produces complete synthetic identity packages

**Key classes**:
- `SemanticMasker` — main masking orchestrator
- `SyntheticIdentityFactory` — generates coherent fake identities (Faker + custom providers)
- `DateShifter` — consistent date/age shifting per session
- `HealthcareFakerProviders` — custom Faker providers for MRN, NPI, health plan IDs

### C3: Vault (`phi_redactor.vault`)

**Responsibility**: Encrypted local storage for PHI ↔ synthetic mappings.

**Design**:
- SQLite database with Fernet-encrypted value columns
- Session-scoped token maps for consistency across multi-turn conversations
- PBKDF2HMAC key derivation from machine key or user passphrase
- MultiFernet for key rotation
- Background cleanup of expired sessions

**Key classes**:
- `PhiVault` — main vault interface (create/read/cleanup)
- `VaultEncryption` — Fernet encryption/decryption, key management
- `SessionTokenMap` — session-scoped O(1) lookup for redaction/re-hydration

### C4: Proxy Server (`phi_redactor.proxy`)

**Responsibility**: Transparent HTTP reverse proxy with PHI interception.

**Design**:
- FastAPI application with route-level handlers (not middleware) for full request/response control
- Provider-specific adapters translate between API formats
- `httpx.AsyncClient` with connection pooling for upstream communication
- Streaming re-hydration via sliding window buffer (3-5 tokens lookback)
- Pre-built trie from session's known synthetic entities for O(1) streaming match

**Key classes**:
- `ProxyApp` — FastAPI application factory
- `OpenAIAdapter` — handles OpenAI API format translation + SSE parsing
- `AnthropicAdapter` — handles Anthropic API format + named SSE events
- `StreamRehydrator` — buffered SSE chunk processor for re-hydration
- `SessionManager` — X-Session-ID tracking, timeouts, cleanup

### C5: Audit Trail (`phi_redactor.audit`)

**Responsibility**: Tamper-evident logging and compliance report generation.

**Design**:
- Append-only JSON Lines file with hash-chain integrity
- Each entry's hash includes previous entry's hash
- Compliance report generator produces HIPAA Safe Harbor evidence in MD/HTML/PDF
- Never contains original PHI — only categories, confidence, and metadata

**Key classes**:
- `AuditTrail` — append events, query events, verify chain integrity
- `ComplianceReportGenerator` — generates Safe Harbor attestation documents
- `AuditEvent` — immutable data class for audit entries

### C6: CLI (`phi_redactor.cli`)

**Responsibility**: User-facing command-line interface.

**Design**:
- Click-based CLI with subcommands: `serve`, `redact`, `report`, `audit`, `sessions`, `config`, `plugins`, `health`, `version`
- Supports JSON + human-readable output formats
- Configuration from CLI flags > env vars > config file > defaults

**Key classes**:
- Click command groups and commands in `cli/` module

### C7: Plugin System (`phi_redactor.plugins`)

**Responsibility**: Extensible detection and masking via third-party Python modules.

**Design**:
- Plugins are Python modules in a configured directory (default: `~/.phi-redactor/plugins/`)
- Each plugin registers `EntityRecognizer` and/or `Masker` subclasses
- Plugin loader uses `importlib` with error isolation (failed plugin doesn't crash the system)
- Plugin API: `register_recognizers()` and `register_maskers()` entry points

## Project Structure

### Documentation (this feature)

```text
specs/001-phi-redaction-proxy/
├── plan.md              # This file
├── research.md          # Phase 0 research findings
├── data-model.md        # Entity definitions and relationships
├── quickstart.md        # Getting started guide
├── contracts/
│   └── openapi.yaml     # Full API contract
└── tasks.md             # Phase 2 output (created by /sp.tasks)
```

### Source Code (repository root)

```text
src/
├── phi_redactor/
│   ├── __init__.py              # Package root, public API exports
│   ├── __main__.py              # python -m phi_redactor entry point
│   ├── config.py                # Configuration loading (env/file/CLI)
│   ├── models.py                # Pydantic models (shared data types)
│   │
│   ├── detection/               # C1: Detection Engine
│   │   ├── __init__.py
│   │   ├── engine.py            # PhiDetectionEngine (Presidio wrapper)
│   │   ├── registry.py          # HIPAARecognizerRegistry
│   │   ├── recognizers/         # Custom HIPAA recognizers
│   │   │   ├── __init__.py
│   │   │   ├── mrn.py           # Medical Record Number
│   │   │   ├── health_plan.py   # Health Plan Beneficiary
│   │   │   ├── account.py       # Account Numbers
│   │   │   ├── license.py       # Certificate/License Numbers
│   │   │   ├── vehicle.py       # Vehicle Identifiers (VIN)
│   │   │   ├── device.py        # Device Identifiers (UDI)
│   │   │   ├── biometric.py     # Biometric Identifiers
│   │   │   └── fhir.py          # FHIR Resource PHI Fields
│   │   └── hl7.py               # HL7v2 segment-aware detection
│   │
│   ├── masking/                 # C2: Masking Engine
│   │   ├── __init__.py
│   │   ├── semantic.py          # SemanticMasker
│   │   ├── identity.py          # SyntheticIdentityFactory
│   │   ├── date_shifter.py      # DateShifter
│   │   ├── clustering.py        # IdentityClusterer
│   │   └── providers.py         # Custom Faker healthcare providers
│   │
│   ├── vault/                   # C3: Vault
│   │   ├── __init__.py
│   │   ├── store.py             # PhiVault (SQLite operations)
│   │   ├── encryption.py        # VaultEncryption (Fernet)
│   │   └── session_map.py       # SessionTokenMap (in-memory cache)
│   │
│   ├── proxy/                   # C4: Proxy Server
│   │   ├── __init__.py
│   │   ├── app.py               # ProxyApp (FastAPI factory)
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── openai.py        # OpenAI proxy routes
│   │   │   ├── anthropic.py     # Anthropic proxy routes
│   │   │   ├── management.py    # Management API routes
│   │   │   └── library.py       # Library API routes (redact/rehydrate)
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # BaseProviderAdapter
│   │   │   ├── openai.py        # OpenAIAdapter
│   │   │   └── anthropic.py     # AnthropicAdapter
│   │   ├── streaming.py         # StreamRehydrator
│   │   └── session.py           # SessionManager
│   │
│   ├── audit/                   # C5: Audit Trail
│   │   ├── __init__.py
│   │   ├── trail.py             # AuditTrail (hash-chain log)
│   │   └── reports.py           # ComplianceReportGenerator
│   │
│   ├── cli/                     # C6: CLI
│   │   ├── __init__.py
│   │   ├── main.py              # Click group entry point
│   │   ├── serve.py             # phi-redactor serve
│   │   ├── redact.py            # phi-redactor redact
│   │   ├── report.py            # phi-redactor report
│   │   ├── audit_cmd.py         # phi-redactor audit
│   │   └── sessions.py          # phi-redactor sessions
│   │
│   └── plugins/                 # C7: Plugin System
│       ├── __init__.py
│       └── loader.py            # Plugin discovery and loading
│
tests/
├── conftest.py                  # Shared fixtures
├── unit/
│   ├── test_detection.py        # Detection engine unit tests
│   ├── test_masking.py          # Masking engine unit tests
│   ├── test_vault.py            # Vault encryption/storage tests
│   ├── test_audit.py            # Audit trail tests
│   └── test_streaming.py        # Stream re-hydration tests
├── integration/
│   ├── test_proxy_openai.py     # Full proxy round-trip (OpenAI)
│   ├── test_proxy_anthropic.py  # Full proxy round-trip (Anthropic)
│   ├── test_session_consistency.py  # Multi-turn session tests
│   └── test_compliance.py       # Compliance report generation
└── contract/
    ├── test_openai_contract.py  # OpenAI API contract conformance
    └── test_anthropic_contract.py  # Anthropic API contract conformance
```

**Structure Decision**: Single project (Python package). The product is a library + CLI + embedded server, not a separate frontend/backend. The dashboard (P3) will be a static HTML page served by the same FastAPI server, not a separate frontend project.

## Key Design Decisions

### D1: Route-Level Handlers Over Middleware

**Decision**: Use explicit FastAPI route handlers instead of ASGI middleware for request interception.

**Rationale**: ASGI middleware cannot access `StreamingResponse` body content (it's an async iterator). Route-level handlers give full control over request parsing, PHI detection, response construction, and streaming chunk processing. Research confirmed this is the only viable pattern for SSE re-hydration.

### D2: Fernet + SQLite Over SQLCipher

**Decision**: Per-entry Fernet encryption with standard SQLite, not SQLCipher.

**Rationale**: SQLCipher requires native C library compilation, platform-specific builds, and breaks the `pip install` simplicity promise. Fernet is pure Python (via `cryptography`), provides per-entry encryption with HMAC authentication, and supports key rotation via MultiFernet. Performance is sub-1ms per entry which meets our requirements.

### D3: Sliding Window Buffer for Streaming Re-Hydration

**Decision**: 3-5 token sliding window buffer with pre-built trie for synthetic entity matching during SSE streaming.

**Rationale**: Synthetic names can be split across streaming chunks (e.g., "Sar" | "ah" | " Ch" | "en"). A buffer accumulates tokens and runs re-hydration matching on the full buffer, emitting only the "safe prefix" that can't be part of an in-progress entity. Pre-built trie from session's known synthetic entities enables O(1) prefix matching. This adds <100ms latency while maintaining streaming behavior.

### D4: Consistent Date/Age Shift Per Session

**Decision**: Random but consistent offset per session (MIMIC-III approach) for date and age shifting.

**Rationale**: Preserves temporal relationships (admission before discharge, age-appropriate treatment patterns) while fully de-identifying. All dates for the same patient shift by the same offset within a session. Age shift capped at ±5 years to preserve clinical age-group relevance (pediatric stays pediatric, geriatric stays geriatric).

### D5: Hash-Chain Audit Trail

**Decision**: Append-only JSON Lines with SHA-256 hash chain for tamper evidence.

**Rationale**: HIPAA 45 CFR 164.312(b) requires audit controls. A hash chain (each entry's hash includes the previous entry's hash) provides tamper evidence without requiring a blockchain or external service. JSON Lines format enables efficient append and line-by-line querying. This meets the compliance evidence requirement for HIPAA Safe Harbor attestation.

### D6: Fail-Safe Default (Block Over Leak)

**Decision**: If the detection engine encounters any error, the proxy blocks the request rather than forwarding potentially unredacted PHI.

**Rationale**: In a HIPAA-regulated context, a false negative (missed PHI sent to LLM) is catastrophically worse than a false positive (blocked request). The fail-safe principle means the system errs on the side of caution. This can be overridden in configuration for development/testing, but the default protects against data breaches.

## Complexity Tracking

No constitution violations detected. No complexity justifications required.
