# Phase 0: Research Findings — PHI Redaction Proxy

**Branch**: `001-phi-redaction-proxy` | **Date**: 2026-02-26

## R1: PHI Detection Engine Architecture

### Decision: Microsoft Presidio v2.2+ as detection foundation, extended with 8 custom healthcare recognizers

**Rationale**: Presidio provides a production-grade, pluggable PII detection framework with AnalyzerEngine → RecognizerRegistry → NlpEngine architecture. It covers ~8-10 of the 18 HIPAA identifiers out of the box (person names, phone numbers, email, SSN, URL, IP address, dates, US driver's license). The remaining identifiers require custom recognizers, which Presidio's `EntityRecognizer` base class makes straightforward.

**Alternatives considered**:
- **AWS Comprehend Medical**: Cloud-only — PHI leaves the machine, violating the core zero-trust architecture. Vendor lock-in.
- **Google Cloud DLP**: Same cloud dependency issue. Generic PII focus, not healthcare-native.
- **Philter (UCSF)**: Academic tool, not actively maintained, Java-based. Hard to integrate into Python ecosystem.
- **Custom from scratch**: Unnecessary — Presidio's recognizer registry pattern provides the extensibility we need without rebuilding NER infrastructure.

### Custom Recognizers Required (8)

| # | Identifier | Detection Method | Presidio Built-in? |
|---|-----------|-----------------|-------------------|
| 1 | Medical Record Numbers (MRN) | Regex + context keywords | No |
| 2 | Health Plan Beneficiary Numbers | Regex + context keywords | No |
| 3 | Account Numbers | Regex + context ("account", "billing") | No |
| 4 | Certificate/License Numbers | Regex + context ("license", "DEA") | No |
| 5 | Vehicle Identifiers (VIN) | Regex (17-char VIN pattern) | No |
| 6 | Device Identifiers (UDI) | Regex (GS1/HIBCC/ICCBBA patterns) | No |
| 7 | Biometric Identifiers | Keyword + context detection | No |
| 8 | FHIR/HL7 Resource PHI Fields | Schema-aware JSON/segment parsing | No |

## R2: NLP Model Selection

### Decision: spaCy `en_core_web_lg` as primary NER model

**Rationale**: Best balance of accuracy and performance for person names, locations, and organizations. 560K word vectors, CNN pipeline, ~10ms/doc for typical clinical note length. Presidio's `SpacyNlpEngine` integrates it natively.

**Alternatives considered**:
- **SciSpaCy**: Targets biomedical entities (diseases, chemicals, genes) — NOT PHI identifiers. Useful as a supplemental recognizer to reduce false positives on clinical terms, not as the primary NER.
- **medspaCy**: Adds clinical section detection and negation context. Valuable as a supplementary component for context-aware false positive reduction, not as primary NER.
- **Transformer-based models (e.g., BioBERT, ClinicalBERT)**: Higher accuracy but 10-100x slower. Would break the <100ms latency target. Can be offered as an optional high-accuracy mode.

### Supplementary: medspaCy for context enhancement

medspaCy's section detection (identifying "Chief Complaint", "Past Medical History", etc.) helps distinguish PHI from clinical terminology. A clinical note saying "Patient has diabetes" contains PHI context, while "Diabetes is a metabolic disease" does not. This reduces false positives.

## R3: Semantic Masking Strategy

### Decision: Faker-based synthetic data generation with custom healthcare providers

**Rationale**: Faker v40+ provides 60+ locale support for culturally diverse name generation, plus built-in providers for addresses, SSNs, phone numbers, dates, emails, URLs, and IP addresses. Custom `BaseProvider` subclasses will generate healthcare-specific identifiers (MRNs, health plan IDs, NPIs).

**Key design decisions**:
- **Date shifting**: Consistent random offset per session (MIMIC-III approach). All dates for the same patient shift by the same offset, preserving temporal relationships (e.g., admission before discharge).
- **Age shifting**: Within ±5 years, capped to preserve age-group clinical relevance (pediatric stays pediatric, geriatric stays geriatric).
- **Name replacement**: Culturally diverse via Faker's multi-locale support. Same patient always gets the same synthetic name within a session.
- **SSN generation**: Structurally valid format (XXX-XX-XXXX) but using known-invalid area numbers (e.g., 987-XX-XXXX range reserved for advertising).
- **MRN generation**: Configurable format to match institution patterns (default: 8-digit numeric).

**Alternatives considered**:
- **Synthetic Data Vault (SDV)**: Overkill — designed for tabular dataset synthesis, not single-entity replacement.
- **LLM-based generation**: Would require an LLM call for each replacement — adds latency, cost, and complexity. Faker is deterministic and fast.

## R4: Vault Encryption Architecture

### Decision: Fernet symmetric encryption + standard SQLite (not SQLCipher)

**Rationale**: Fernet (from Python `cryptography` library) provides per-entry AES-128-CBC encryption with HMAC authentication. Combined with standard SQLite, this keeps the installation to a simple `pip install` without native compilation dependencies. SQLCipher would require platform-specific binary builds, breaking the "60-second install" promise.

**Key design**:
- **Key derivation**: PBKDF2HMAC with SHA256, 480,000 iterations, from user passphrase or auto-generated machine key
- **Key rotation**: MultiFernet supports transparent rotation — new entries use new key, old entries still decryptable
- **Storage**: SQLite for the index/metadata, Fernet-encrypted blobs for PHI values
- **Performance**: Sub-1ms lookups on standard SQLite; Fernet encrypt/decrypt adds <0.1ms per entry

**Alternatives considered**:
- **SQLCipher**: Transparent full-database encryption, but requires native compilation (C library). Breaks `pip install` simplicity.
- **File-based vault (JSON + Fernet)**: No concurrent access support, no efficient lookup for large session maps.
- **HashiCorp Vault**: External service dependency — overkill for local developer use.

## R5: LLM Proxy Architecture

### Decision: FastAPI with route-level handlers + httpx AsyncClient

**Rationale**: FastAPI provides async request handling, automatic OpenAPI docs, and Pydantic validation. Route-level handlers (not middleware) give us full control over request/response interception. httpx AsyncClient provides connection pooling and streaming support for upstream LLM calls.

**Key architecture**:
```
Client → FastAPI route handler → PHI detection → Masking → httpx → LLM API
                                                                    ↓
Client ← Re-hydration ← Response processing ← httpx streaming ← LLM API
```

**Provider routing**:
- `/openai/v1/*` → OpenAI API format
- `/anthropic/v1/*` → Anthropic API format
- `/v1/*` → Auto-detect or configured default provider

**Streaming re-hydration**:
- Sliding window buffer accumulating 3-5 tokens before emission
- Lookback window of ~50 characters matching max PHI entity length
- Pre-built trie from session's known synthetic entities for fast matching
- Flush remaining buffer on stream completion
- Target: <100ms added latency from buffering

**Alternatives considered**:
- **ASGI middleware approach**: Cannot intercept StreamingResponse body (it's an async iterator). Route-level handlers are necessary.
- **aiohttp**: Less integrated ecosystem than FastAPI, no automatic OpenAPI docs, slightly more boilerplate.
- **mitmproxy**: Full HTTPS interception proxy — too heavy, requires certificate installation. We want a simple reverse proxy.

## R6: Session Management

### Decision: X-Session-ID header with conversation-hash fallback

**Rationale**: Explicit session IDs via custom header give clients control. Fallback to hashing the first message content provides automatic session detection for clients that don't send headers.

**Key design**:
- **Session lifecycle**: 30-minute idle timeout, 24-hour max lifetime
- **Storage**: In-memory dict for single-instance (default); extensible to Redis for future multi-instance
- **Cleanup**: Background asyncio task every 5 minutes
- **Session entity registry**: Maps original PHI → synthetic replacements, persists across turns

## R7: HIPAA Compliance & Audit

### Decision: Hash-chain append-only audit log with Safe Harbor evidence generation

**Rationale**: HIPAA 45 CFR 164.312(b) requires audit controls. A hash-chain (each entry's hash includes the previous entry's hash) provides tamper evidence. Append-only log files prevent modification of historical entries.

**Key design**:
- **Audit entry schema**: timestamp, session_id, redaction_category (HIPAA type), confidence_score, action (redacted/flagged/passed), entry_hash, previous_hash
- **Never logged**: Original PHI values
- **Report generation**: Markdown + HTML + PDF (via weasyprint or reportlab) compliance reports
- **Safe Harbor attestation**: Covers methodology description, all 18 identifier categories, accuracy metrics, sample anonymized logs

**Production benchmark target**: Recall ≥ 99% (based on Philter 99.46%, Providence Health <1% leak rate). The i2b2 2014 dataset with 25 PHI subcategories is the canonical evaluation benchmark.

## R8: API Contract Differences

### OpenAI vs Anthropic Format Differences

| Aspect | OpenAI | Anthropic |
|--------|--------|-----------|
| Auth header | `Authorization: Bearer sk-...` | `x-api-key: sk-ant-...` + `anthropic-version: 2023-06-01` |
| System prompt | `messages[0].role = "system"` | Top-level `system` field |
| Response structure | `choices[].message.content` | `content[].text` (typed blocks) |
| Streaming format | `data: {JSON}\n\n` with `data: [DONE]` | Named SSE events (message_start, content_block_delta, etc.) |
| Content in stream | `choices[].delta.content` | `delta.text` in content_block_delta events |

The proxy must translate between these formats transparently. The redaction/re-hydration pipeline operates on the text content regardless of the wrapper format.

## Unresolved Items

None — all NEEDS CLARIFICATION items have been resolved through research.
