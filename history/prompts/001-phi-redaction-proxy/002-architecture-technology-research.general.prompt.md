---
id: 002
title: Architecture Technology Research for PHI Redactor
stage: general
date: 2026-02-26
surface: agent
model: claude-opus-4-6
feature: 001-phi-redaction-proxy
branch: master
user: TechTiesIbrahim
command: research
labels: ["presidio", "spacy", "faker", "encryption", "architecture", "research"]
links:
  spec: specs/001-phi-redaction-proxy/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - history/prompts/001-phi-redaction-proxy/002-architecture-technology-research.general.prompt.md
tests:
  - none (research only)
---

## Prompt

Research task for phi-redactor project architecture. Do NOT write any code. Research only.

I need detailed technical findings on:

1. **Microsoft Presidio architecture** for PHI/PII detection:
   - How does the Presidio AnalyzerEngine work? What's the recognizer registry pattern?
   - How to add custom recognizers (for healthcare-specific patterns like MRNs, FHIR references)?
   - What are Presidio's built-in recognizers and which HIPAA identifiers do they cover?
   - What are the performance characteristics (latency per text chunk, memory usage)?
   - How does Presidio's AnonymizerEngine work for replacement?
   - Latest version and Python compatibility (Python 3.11+)?

2. **spaCy for healthcare NER**:
   - Which spaCy models work best for clinical/medical text (en_core_web_lg, SciSpaCy, etc.)?
   - How does spaCy integrate with Presidio (NlpEngine)?
   - Performance of spaCy NER on clinical text — is it accurate enough for PHI detection?
   - SciSpaCy models — are there healthcare-specific NER models available?

3. **Synthetic data generation for semantic masking**:
   - Faker library — does it have healthcare-specific providers (names, SSNs, MRNs, addresses)?
   - How to generate clinically coherent synthetic replacements (age-shifted but clinically relevant, culturally diverse names)?
   - Date shifting strategies — consistent offset per session vs. random per date?
   - Best practices for generating structurally valid but fake SSNs, MRNs, phone numbers?

4. **Encryption for vault storage**:
   - Python `cryptography` library — Fernet symmetric encryption for SQLite at-rest encryption?
   - Or SQLCipher for transparent SQLite encryption?
   - Key derivation from user passphrase (PBKDF2/Argon2)?
   - Performance impact of encrypted lookups?

Return detailed findings with specific version numbers, API patterns, and code architecture recommendations.

## Response snapshot

Comprehensive research findings delivered covering all four areas:

1. **Presidio**: v2.2.361 (Feb 2026), Python 3.10-3.13. AnalyzerEngine uses RecognizerRegistry + NlpEngine + ContextAwareEnhancer. Covers ~8-10 of 18 HIPAA identifiers natively; MRNs, health plan IDs, device IDs, etc. require custom recognizers. AnonymizerEngine supports replace/redact/hash/mask/encrypt operators plus custom operators. Performance: <10ms/1000 tokens.

2. **spaCy/SciSpaCy**: en_core_web_lg recommended as primary NlpEngine for PHI (names, locations, dates). SciSpaCy (v0.5.5) provides biomedical NER but targets medical entities not PHI. medspaCy adds clinical section detection and negation. Presidio supports one NLP model per language; additional models wrapped as recognizers.

3. **Faker**: v40.5.1, built-in SSN/name/address/phone providers. No healthcare-specific providers (MRN, NPI, health plan ID) -- requires custom BaseProvider subclasses. Multi-locale support for culturally diverse names. Date shifting: consistent offset per session recommended (MIMIC approach).

4. **Encryption**: Fernet + standard SQLite recommended over SQLCipher. Fernet (cryptography v44.x) provides per-entry encryption, MultiFernet key rotation, PBKDF2HMAC key derivation (1.2M iterations). SQLCipher requires native compilation breaking pip install simplicity. Sub-1ms lookups achievable.

8 custom recognizers identified as needed for full HIPAA coverage.

## Outcome

- Impact: Established technology stack and identified gaps for all core components
- Tests: none (research only)
- Files: PHR record created
- Next prompts: /sp.plan to create detailed implementation plan using these findings, custom recognizer design, vault schema design
- Reflection: Presidio provides strong framework but significant custom work needed for healthcare-specific PHI detection. Fernet clearly wins over SQLCipher for pip-installable tool.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): validate Presidio + en_core_web_lg accuracy on sample clinical text with all 18 HIPAA identifier types
