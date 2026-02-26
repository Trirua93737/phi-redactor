# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-27

### Added

- PHI detection engine with all 18 HIPAA identifiers using Presidio + spaCy
- Semantic masking with deterministic, identity-preserving fake data
- Encrypted vault (Fernet) for PHI-to-mask mappings with session isolation
- Tamper-evident audit trail with SHA-256 hash chains
- FastAPI reverse proxy with Anthropic and OpenAI adapters
- Streaming support for LLM responses with real-time re-identification
- Click-based CLI for session management, vault stats, and Safe Harbor reports
- Real-time monitoring dashboard
- FHIR R4 and HL7v2 recognizers via plugin system
- CI pipeline for Python 3.11, 3.12, 3.13
- Comprehensive test suite (detection, masking, vault, proxy, compliance)

[0.1.0]: https://github.com/DilawarShafiq/phi-redactor/releases/tag/v0.1.0