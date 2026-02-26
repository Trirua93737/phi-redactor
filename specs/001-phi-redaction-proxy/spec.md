# Feature Specification: PHI Redaction Proxy for AI/LLM Interactions

**Feature Branch**: `001-phi-redaction-proxy`
**Created**: 2026-02-26
**Status**: Draft
**Input**: User description: "An open-source, HIPAA-native PHI redaction proxy — a CLI tool and Python library that sits between any AI agent/application and LLM APIs to intercept, detect, and redact Protected Health Information in real-time before it reaches the LLM, then re-hydrates responses with original values locally."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One-Command PHI-Safe LLM Proxy (Priority: P1)

A healthcare AI developer installs phi-redactor, starts the proxy with a single command, points their existing OpenAI/Anthropic client at the local proxy endpoint, and continues working as normal. All PHI in their prompts is automatically detected and replaced with clinically coherent synthetic values before leaving the machine. LLM responses containing synthetic tokens are re-hydrated back to the original values before reaching the developer's application. The developer's existing code requires zero changes beyond updating the base URL.

**Why this priority**: This is the core value proposition — zero-friction PHI protection for any AI workflow. Without this, nothing else matters. A healthcare developer should go from `pip install` to protected in under 60 seconds.

**Independent Test**: Can be fully tested by starting the proxy, sending a prompt containing patient names/SSNs/MRNs through it to any LLM, and verifying (a) the LLM never receives raw PHI, (b) the developer's application receives a coherent response with original values restored.

**Acceptance Scenarios**:

1. **Given** the proxy is running and configured with an upstream LLM provider, **When** a developer sends a prompt containing "John Smith, SSN 123-45-6789, MRN 00123456, diagnosed with Type 2 Diabetes on 03/15/1998" through the proxy, **Then** the upstream LLM receives a prompt where all PHI identifiers are replaced with synthetic but clinically coherent values (e.g., a different realistic name, a structurally valid but fake SSN, a different MRN, a shifted date), and the developer's application receives the LLM response with original values restored.

2. **Given** the proxy is running, **When** a developer configures their OpenAI Python client with `base_url="http://localhost:8080/v1"`, **Then** all existing OpenAI SDK calls (chat completions, embeddings) work identically to calling the real API, with PHI transparently redacted and re-hydrated.

3. **Given** the proxy is running in streaming mode, **When** a developer requests a streaming chat completion containing PHI references, **Then** each SSE chunk is processed and re-hydrated in real-time without breaking the streaming contract.

4. **Given** a multi-turn conversation with consistent patient references, **When** the same patient name appears across 5+ messages, **Then** the proxy uses the same synthetic replacement consistently throughout the session, maintaining conversation coherence for the LLM.

---

### User Story 2 - Multi-Layer PHI Detection Covering All 18 HIPAA Identifiers (Priority: P1)

A compliance officer needs assurance that the system detects and redacts all 18 categories of Protected Health Information as defined by the HIPAA Safe Harbor method, plus common clinical data patterns found in healthcare workflows. The detection engine combines pattern-based recognition (regex for structured identifiers like SSNs, MRNs, phone numbers, dates) with named entity recognition (NER for person names, locations, organizations) and healthcare-specific recognizers (FHIR resource references, HL7 message segments, ICD/CPT codes in context).

**Why this priority**: Detection accuracy is the foundation of trust. If the system misses PHI, it's a compliance liability. If it over-redacts, it's unusable. This must be bulletproof from day one.

**Independent Test**: Can be tested by running a PHI detection benchmark against a corpus of synthetic clinical documents containing all 18 HIPAA identifier types and measuring precision/recall.

**Acceptance Scenarios**:

1. **Given** a text block containing examples of all 18 HIPAA Safe Harbor identifiers (names, geographic data, dates, phone numbers, fax numbers, email addresses, SSNs, MRNs, health plan beneficiary numbers, account numbers, certificate/license numbers, vehicle identifiers, device identifiers, web URLs, IP addresses, biometric identifiers, full-face photos, any other unique identifying number), **When** the detection engine processes it, **Then** each identifier is detected with a confidence score and categorized by HIPAA type.

2. **Given** a clinical note with embedded PHI in natural language (e.g., "The patient, Maria Garcia, presented to Springfield General on January 15th..."), **When** the detection engine processes it, **Then** person names, facility names, and dates are detected even when not in a structured format.

3. **Given** an HL7 FHIR JSON resource (e.g., a Patient resource with name, address, identifiers), **When** the detection engine processes it, **Then** PHI fields are identified based on FHIR resource schema awareness, not just pattern matching.

4. **Given** a text with PHI-like patterns that are NOT actually PHI (e.g., "ICD-10 code E11.9" as a diagnosis code, or "the study enrolled 123 patients"), **When** the detection engine processes it, **Then** these are not flagged as PHI, maintaining a false-positive rate below an acceptable threshold.

---

### User Story 3 - Semantic Masking with Clinically Coherent Synthetic Replacements (Priority: P1)

Instead of replacing PHI with opaque tokens like `[REDACTED]` or `[PATIENT_NAME_1]`, the system generates clinically coherent synthetic replacements that preserve the medical reasoning context. A patient named "John Smith, 67-year-old male with Type 2 Diabetes" becomes "Sarah Chen, 54-year-old female with Type 2 Diabetes" — the LLM can still reason about the clinical scenario because the replacement maintains demographic plausibility and clinical relevance, while the actual identity is completely protected.

**Why this priority**: This is the key differentiator from every existing tool. Opaque redaction (`[REDACTED]`) degrades LLM reasoning quality. Semantic masking means healthcare teams get PHI protection AND high-quality AI outputs. This is why the product wins.

**Independent Test**: Can be tested by sending redacted clinical scenarios to an LLM and comparing response quality (clinical accuracy, completeness) against responses from unredacted originals, measuring that quality degradation is minimal.

**Acceptance Scenarios**:

1. **Given** a clinical note with patient demographics, **When** semantic masking is applied, **Then** names are replaced with culturally diverse synthetic names, ages are shifted within a clinically reasonable range (preserving age-group relevance), dates are shifted by a consistent random offset, and geographic locations are replaced with different but structurally similar locations.

2. **Given** a prompt containing "John Smith, 67M, with HbA1c of 9.2%, on metformin 1000mg BID", **When** semantic masking is applied and the masked text is sent to an LLM asking for treatment recommendations, **Then** the LLM provides clinically appropriate recommendations that are equivalent in quality to what it would produce with the original text.

3. **Given** the same patient referenced across multiple messages in a session, **When** semantic masking is applied, **Then** all references to that patient use the same synthetic identity consistently (same synthetic name, same date shift offset, same synthetic MRN) throughout the session.

---

### User Story 4 - Vault-Based Tokenization with Local Encrypted Storage (Priority: P2)

All mappings between original PHI values and their synthetic replacements are stored in a local encrypted vault that never leaves the developer's machine. The vault maintains session-aware token maps so that multi-turn conversations reference consistent synthetic identities. The vault supports key rotation, automatic expiration of old mappings, and export of anonymized audit data.

**Why this priority**: The vault is essential infrastructure for re-hydration and consistency, but the user doesn't directly interact with it — it works behind the scenes. P2 because the core proxy and detection must work first.

**Independent Test**: Can be tested by verifying that vault files are encrypted at rest, that token lookups are O(1), that session isolation works correctly, and that vault data cannot be read without the encryption key.

**Acceptance Scenarios**:

1. **Given** a PHI value is redacted during a proxy session, **When** the mapping is stored in the vault, **Then** the vault file on disk is encrypted and unreadable without the local encryption key.

2. **Given** a session with 100+ unique PHI values mapped, **When** re-hydration is needed for any value, **Then** the lookup completes in under 1 millisecond.

3. **Given** a session has ended and the configured retention period has passed, **When** the vault cleanup runs, **Then** expired mappings are securely deleted and unrecoverable.

4. **Given** two concurrent proxy sessions for different applications, **When** both sessions process PHI, **Then** their vault mappings are isolated and one session cannot access the other's PHI mappings.

---

### User Story 5 - Compliance-as-Code Audit Trail and Reporting (Priority: P2)

Every redaction event is logged in a tamper-evident audit trail that captures what was redacted (by category, not the actual PHI value), when, with what confidence, and for which session. The system can generate HIPAA Safe Harbor compliance reports, showing that all 18 identifier types are covered and providing evidence of de-identification methodology. These reports are suitable for presenting to auditors, compliance officers, and during HITRUST assessments.

**Why this priority**: Healthcare organizations won't adopt a tool without compliance evidence. This is the "enterprise unlock" — the feature that makes procurement teams say yes.

**Independent Test**: Can be tested by running a batch of redactions and generating a compliance report, then verifying the report contains all required sections and data for a HIPAA Safe Harbor attestation.

**Acceptance Scenarios**:

1. **Given** the proxy has processed 1000 requests containing PHI, **When** a compliance report is generated, **Then** the report shows total redactions by HIPAA identifier category, detection confidence distributions, and session-level summaries without revealing any actual PHI.

2. **Given** the audit trail for a session, **When** reviewed by a compliance officer, **Then** each entry shows: timestamp, redaction category (e.g., "PERSON_NAME"), confidence score, session ID, and action taken (redacted/passed/flagged) — but never the original PHI value.

3. **Given** a request to generate a HIPAA Safe Harbor evidence package, **When** the export command is run, **Then** the system produces a document attesting to coverage of all 18 HIPAA identifiers with methodology description, detection accuracy metrics, and sample anonymized redaction logs.

---

### User Story 6 - Multi-Provider Drop-In Proxy Support (Priority: P2)

The proxy works as a transparent drop-in replacement for OpenAI, Anthropic, Google Vertex AI, and Azure OpenAI API endpoints. Developers configure their existing SDK client to point at the local proxy, and the proxy handles the provider-specific API translation. No code changes beyond the base URL are required.

**Why this priority**: Provider-agnostic support dramatically increases the addressable market. Most healthcare AI teams use multiple providers or switch between them.

**Independent Test**: Can be tested by running the same clinical prompt through the proxy targeting each supported provider and verifying that PHI redaction and re-hydration work correctly regardless of provider-specific API differences.

**Acceptance Scenarios**:

1. **Given** a developer using the OpenAI Python SDK, **When** they set `base_url="http://localhost:8080/openai/v1"`, **Then** all chat completion and embeddings calls work identically with PHI transparently redacted.

2. **Given** a developer using the Anthropic Python SDK, **When** they set `base_url="http://localhost:8080/anthropic/v1"`, **Then** all messages API calls work identically with PHI transparently redacted.

3. **Given** a developer switches from OpenAI to Anthropic mid-project, **When** they change only the base URL and API key configuration, **Then** the vault maintains consistent synthetic identities across provider switches within the same session.

---

### User Story 7 - FHIR-Native Healthcare Data Understanding (Priority: P3)

The system natively understands HL7 FHIR resources, CDA documents, and HL7v2 messages. When these structured healthcare data formats appear in prompts (common when building clinical AI applications), the system uses schema-aware redaction rather than generic pattern matching, resulting in higher accuracy and fewer false positives.

**Why this priority**: Deep healthcare format understanding differentiates this from generic PII tools. However, most early adopters will start with free-text clinical notes, making this a P3 for initial launch.

**Independent Test**: Can be tested by passing FHIR Patient, Encounter, and Observation resources through the system and verifying that PHI fields are redacted based on FHIR schema definitions, not just pattern matching.

**Acceptance Scenarios**:

1. **Given** a FHIR Patient resource JSON containing name, birthDate, address, and identifier fields, **When** processed by the system, **Then** each PHI field is detected and redacted based on the FHIR Patient schema definition, and non-PHI fields (resourceType, active status, clinical codes) are preserved unchanged.

2. **Given** an HL7v2 ADT message with PID (Patient Identification) and NK1 (Next of Kin) segments, **When** processed by the system, **Then** PHI fields within those segments are identified by segment/field position (e.g., PID.5 = Patient Name) and redacted, while non-PHI segments are passed through.

3. **Given** a mixed prompt containing both free-text clinical notes and embedded FHIR resource references, **When** processed by the system, **Then** both the free-text PHI and the structured FHIR PHI are detected and redacted using the appropriate method for each.

---

### User Story 8 - Plugin Architecture for Custom Redaction Rules (Priority: P3)

Organizations can extend the detection and masking engine with custom rules for proprietary identifier formats, institution-specific patterns (e.g., custom MRN formats, internal patient ID schemes), and domain-specific entities. Plugins are Python modules that register recognizers and maskers with a simple API.

**Why this priority**: Extensibility is critical for enterprise adoption (every health system has unique identifier formats), but the core product must work well out-of-the-box first.

**Independent Test**: Can be tested by creating a sample plugin that detects a custom identifier format, registering it, and verifying it integrates with the detection and masking pipeline.

**Acceptance Scenarios**:

1. **Given** a developer creates a Python plugin module with a custom recognizer class, **When** the plugin is placed in the configured plugins directory and the proxy restarts, **Then** the custom recognizer is automatically loaded and integrated into the detection pipeline.

2. **Given** a hospital uses a proprietary patient ID format "HOSP-XXXX-YYYY", **When** a plugin is written to recognize this pattern, **Then** the system detects and redacts these IDs alongside standard HIPAA identifiers.

3. **Given** an active plugin raises an error during detection, **When** the proxy processes a request, **Then** the error is logged, the plugin is bypassed for that request, and all other detection continues normally without disruption.

---

### User Story 9 - Web Dashboard for Monitoring and Compliance Posture (Priority: P3)

A lightweight web dashboard provides real-time visibility into the proxy's operation: active sessions, redaction statistics, detection confidence distributions, audit trail viewer, and compliance posture summary. The dashboard is optional and runs as a separate process.

**Why this priority**: Visual monitoring is impressive for demos and useful for compliance teams, but the CLI-first experience is the core product. The dashboard is a "wow factor" addition for later.

**Independent Test**: Can be tested by starting the dashboard, processing requests through the proxy, and verifying the dashboard updates in real-time with accurate statistics.

**Acceptance Scenarios**:

1. **Given** the dashboard is running alongside the proxy, **When** PHI redaction events occur, **Then** the dashboard displays updated statistics within 2 seconds including: total requests, total redactions by category, and average detection confidence.

2. **Given** a compliance officer accesses the dashboard, **When** they navigate to the audit trail view, **Then** they can filter events by time range, session ID, and redaction category, and export filtered results.

3. **Given** the proxy is running without the dashboard, **When** the dashboard is started later, **Then** it loads historical data from the audit trail and displays the full history without data loss.

---

### Edge Cases

- What happens when the proxy cannot reach the upstream LLM? The proxy returns a clear error to the client application with the original request queued for retry, and no PHI is leaked in error messages.
- What happens when a text contains PHI in a language other than English? The system flags non-English text segments and applies conservative redaction (higher sensitivity), logging a warning that multilingual detection may have lower confidence.
- What happens when the LLM response introduces NEW patient names not in the original prompt? The re-hydration step only maps known tokens; unexpected PHI-like content in responses is flagged but not modified, with a warning logged.
- What happens when PHI is embedded in code snippets (e.g., SQL queries with patient names in WHERE clauses)? The detection engine scans all text including code blocks and SQL strings, recognizing PHI within programming constructs.
- What happens when a vault grows very large (millions of mappings)? The vault implements automatic partitioning by session and time-based expiration, with configurable retention limits.
- What happens when the system receives binary data or images in the prompt? Binary and image content is passed through with a warning logged; PHI redaction only applies to text content. Image PHI detection is flagged as a future capability.
- What happens when network latency to the LLM is high? The proxy adds minimal overhead (target: under 50ms for redaction processing) and uses async I/O to avoid blocking.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST intercept all HTTP/HTTPS requests between a client application and configured LLM API endpoints, acting as a transparent forward proxy.
- **FR-002**: System MUST detect all 18 HIPAA Safe Harbor identifier categories in text content with a minimum recall of 95% on standard de-identification benchmarks.
- **FR-003**: System MUST replace detected PHI with clinically coherent synthetic values that preserve the semantic context needed for LLM reasoning (semantic masking).
- **FR-004**: System MUST maintain a local encrypted vault mapping original PHI to synthetic replacements, ensuring consistent synthetic identities within a session.
- **FR-005**: System MUST re-hydrate LLM responses by replacing synthetic tokens with original PHI values before returning to the client application.
- **FR-006**: System MUST support streaming (SSE) responses, processing and re-hydrating tokens in real-time as chunks arrive.
- **FR-007**: System MUST provide OpenAI-compatible, Anthropic-compatible, Google Vertex AI-compatible, and Azure OpenAI-compatible proxy endpoints.
- **FR-008**: System MUST log every redaction event in a tamper-evident audit trail with: timestamp, redaction category, confidence score, session ID, and action taken — but never the original PHI value.
- **FR-009**: System MUST generate HIPAA Safe Harbor compliance evidence reports on demand.
- **FR-010**: System MUST provide a CLI interface for starting/stopping the proxy, configuring providers, managing sessions, and generating reports.
- **FR-011**: System MUST support plugin-based extension of the detection and masking pipeline via Python modules.
- **FR-012**: System MUST encrypt vault data at rest using industry-standard encryption.
- **FR-013**: System MUST support concurrent sessions with isolated vault namespaces.
- **FR-014**: System MUST operate entirely locally — no PHI data is transmitted to any external service other than the configured LLM endpoint (and only after redaction).
- **FR-015**: System MUST be installable via `pip install phi-redactor` and operational within 60 seconds of installation.
- **FR-016**: System MUST provide a Python library API for programmatic integration (not just CLI/proxy usage).
- **FR-017**: System MUST support configuration via environment variables, config files, and CLI flags with clear precedence order.
- **FR-018**: System MUST natively parse and redact FHIR JSON resources, HL7v2 messages, and CDA XML documents using schema-aware field identification.
- **FR-019**: System MUST provide a confidence score for each detection, allowing users to configure sensitivity thresholds.
- **FR-020**: System MUST handle graceful degradation — if the detection engine encounters an error, it should fail safe (block the request rather than send unredacted PHI).

### Key Entities

- **Session**: A logical grouping of proxy requests from a single client, maintaining consistent synthetic identity mappings across the conversation.
- **PHI Token**: A detected piece of Protected Health Information, categorized by HIPAA type, with a confidence score and location in the source text.
- **Synthetic Identity**: A coherent set of synthetic replacement values (name, demographics, identifiers) that maintains clinical plausibility.
- **Vault Entry**: An encrypted mapping between an original PHI value and its synthetic replacement, scoped to a session with an expiration timestamp.
- **Redaction Event**: An audit log entry recording that a redaction occurred, including category, confidence, timestamp, and session — but never the original value.
- **Provider Endpoint**: A configured upstream LLM API with provider type, base URL, authentication, and rate limits.
- **Plugin**: A Python module registering custom recognizers and/or maskers with the detection pipeline.
- **Compliance Report**: A generated document attesting to de-identification coverage, methodology, and accuracy metrics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can go from `pip install phi-redactor` to a running PHI-protected proxy in under 60 seconds with a single command.
- **SC-002**: The system detects at least 95% of PHI instances across all 18 HIPAA Safe Harbor categories on standard de-identification benchmarks (i2b2, n2c2).
- **SC-003**: False positive rate (non-PHI incorrectly flagged) stays below 5% on clinical text benchmarks.
- **SC-004**: LLM response quality with semantic masking is within 5% of unmasked baseline quality on clinical reasoning tasks (measured by clinician evaluation or automated clinical NLP metrics).
- **SC-005**: Proxy adds less than 100 milliseconds of latency per request for redaction and re-hydration processing.
- **SC-006**: System handles at least 50 concurrent sessions without performance degradation.
- **SC-007**: Round-trip re-hydration accuracy (synthetic tokens correctly mapped back to originals) is 99%+ even when the LLM paraphrases or restructures the response.
- **SC-008**: Compliance reports contain all required elements for a HIPAA Safe Harbor attestation as verified by a compliance checklist.
- **SC-009**: The system operates with zero PHI data transmitted to any external service other than the configured LLM (post-redaction).
- **SC-010**: GitHub repository achieves 100+ stars within 90 days of public launch, indicating community validation and developer interest.

## Assumptions

- Users have Python 3.11 or later installed on their machines.
- Users have valid API keys for their chosen LLM provider(s).
- The primary use case is English-language clinical text; multilingual support will be a future enhancement.
- The local machine where the proxy runs is considered a trusted environment (the user controls physical access).
- Internet connectivity is available for reaching upstream LLM APIs (the proxy is not an offline LLM replacement).
- The spaCy NER models and Presidio framework provide a sufficient foundation for PHI detection, extended with custom healthcare-specific recognizers.
- SQLite provides sufficient performance for vault operations at the expected scale (single developer to small team usage).
- The primary deployment model is single-user/developer workstation; multi-tenant server deployment is a future consideration.

## Dependencies

- **Microsoft Presidio**: Foundation for PII/PHI detection engine, extended with healthcare-specific recognizers.
- **spaCy**: NLP pipeline for named entity recognition, with healthcare-specific model training.
- **FastAPI**: Async HTTP framework for the proxy server.
- **httpx**: Async HTTP client for upstream LLM API communication.
- **SQLite + cryptography**: Local encrypted vault for token mappings.
- **Click**: CLI framework for the command-line interface.
- **LLM Provider APIs**: OpenAI, Anthropic, Google Vertex AI, Azure OpenAI — the system proxies to these upstream services.

## Out of Scope

- Image-based PHI detection (OCR of scanned documents, photos) — text-only for initial release.
- Real-time audio/video PHI redaction.
- Multi-tenant server deployment with user management.
- Custom NER model training workflows (users can bring pre-trained models via plugins).
- Replacement of the LLM itself — this is a proxy, not an LLM.
- De-identification of data at rest (databases, file systems) — this is for LLM interaction streams only.
- GDPR, CCPA, or non-HIPAA privacy regulation compliance (HIPAA-first, others are future).
