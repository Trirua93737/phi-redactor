# Data Model: PHI Redaction Proxy

**Branch**: `001-phi-redaction-proxy` | **Date**: 2026-02-26

## Entity Relationship Overview

```
Session 1──────* VaultEntry
Session 1──────* RedactionEvent
VaultEntry *───1 PHIToken (detected)
VaultEntry *───1 SyntheticIdentity (replacement)
RedactionEvent *──1 VaultEntry
ProviderEndpoint 1──────* Session
Plugin 1──────* EntityRecognizer (registered)
ComplianceReport *──────* RedactionEvent (aggregated)
```

## Entities

### Session

Represents a logical conversation grouping across multiple API proxy requests.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | UUID | Unique session identifier | Primary key, auto-generated |
| created_at | DateTime | Session creation timestamp | UTC, immutable |
| last_active_at | DateTime | Last request timestamp | UTC, updated on each request |
| expires_at | DateTime | Session expiration time | created_at + max_lifetime (24h default) |
| idle_timeout_seconds | Integer | Idle timeout in seconds | Default: 1800 (30 min) |
| provider | String | Active LLM provider identifier | One of: openai, anthropic, google, azure |
| status | Enum | Session lifecycle state | active, expired, closed |
| date_shift_offset_days | Integer | Consistent date shift for this session | Random ±365, set at creation |
| age_shift_offset_years | Integer | Consistent age shift for this session | Random ±5, set at creation |
| metadata | JSON | Arbitrary session metadata | Optional |

**State transitions**: `active` → `expired` (idle/max timeout) | `active` → `closed` (explicit close)

### PHIToken

A detected piece of Protected Health Information in source text.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | UUID | Unique detection identifier | Primary key |
| session_id | UUID | Parent session | Foreign key → Session.id |
| category | Enum | HIPAA Safe Harbor category | One of 18 categories (see below) |
| original_text | String | The detected PHI value | Encrypted at rest, never logged |
| start_position | Integer | Character offset start in source text | >= 0 |
| end_position | Integer | Character offset end in source text | > start_position |
| confidence | Float | Detection confidence score | 0.0 - 1.0 |
| detection_method | Enum | How it was detected | regex, ner, schema, plugin |
| recognizer_name | String | Which recognizer found it | e.g., "SpacyRecognizer", "SSNRecognizer" |
| context_score | Float | Context-enhanced confidence | 0.0 - 1.0, after context analysis |

**HIPAA Safe Harbor Categories** (Enum values):
1. `PERSON_NAME` — Names
2. `GEOGRAPHIC_DATA` — Geographic subdivisions smaller than state
3. `DATE` — Dates (except year) related to an individual
4. `PHONE_NUMBER` — Phone numbers
5. `FAX_NUMBER` — Fax numbers
6. `EMAIL_ADDRESS` — Email addresses
7. `SSN` — Social Security numbers
8. `MRN` — Medical record numbers
9. `HEALTH_PLAN_ID` — Health plan beneficiary numbers
10. `ACCOUNT_NUMBER` — Account numbers
11. `LICENSE_NUMBER` — Certificate/license numbers
12. `VEHICLE_ID` — Vehicle identifiers and serial numbers
13. `DEVICE_ID` — Device identifiers and serial numbers
14. `WEB_URL` — Web URLs
15. `IP_ADDRESS` — IP addresses
16. `BIOMETRIC_ID` — Biometric identifiers
17. `PHOTO` — Full-face photographs and comparable images
18. `OTHER_UNIQUE_ID` — Any other unique identifying number

### SyntheticIdentity

A coherent set of synthetic replacement values for a detected identity.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | UUID | Unique identity identifier | Primary key |
| session_id | UUID | Parent session | Foreign key → Session.id |
| identity_cluster | String | Groups related PHI for one person | e.g., "patient_1" |
| synthetic_name | String | Generated replacement name | From Faker, consistent per cluster |
| synthetic_dob | Date | Shifted date of birth | Original + session.date_shift_offset_days |
| synthetic_ssn | String | Structurally valid fake SSN | Format: XXX-XX-XXXX, invalid area numbers |
| synthetic_mrn | String | Generated MRN | Configurable format |
| synthetic_phone | String | Generated phone number | From Faker |
| synthetic_email | String | Generated email | From Faker |
| synthetic_address | String | Generated address | From Faker, different state |
| locale | String | Faker locale used | Default: en_US |
| created_at | DateTime | Creation timestamp | UTC |

### VaultEntry

Encrypted mapping between original PHI and its synthetic replacement.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | UUID | Unique entry identifier | Primary key |
| session_id | UUID | Parent session | Foreign key → Session.id |
| original_hash | String | SHA-256 hash of original text | For deduplication within session |
| original_encrypted | Bytes | Fernet-encrypted original PHI value | Never stored in plaintext |
| synthetic_value | String | The synthetic replacement text | Plaintext (not sensitive) |
| phi_category | Enum | HIPAA category | Same enum as PHIToken.category |
| identity_cluster | String | Links to SyntheticIdentity | Nullable, for grouped identities |
| created_at | DateTime | Entry creation time | UTC |
| expires_at | DateTime | Auto-expiration time | session.expires_at by default |

**Indexes**:
- `(session_id, original_hash)` — UNIQUE, for fast dedup lookups
- `(session_id, synthetic_value)` — for re-hydration reverse lookups
- `(expires_at)` — for cleanup queries

### RedactionEvent

Tamper-evident audit log entry for each redaction action.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | Integer | Auto-incrementing event ID | Primary key |
| session_id | UUID | Parent session | Foreign key → Session.id |
| timestamp | DateTime | When redaction occurred | UTC, immutable |
| request_id | UUID | Which proxy request triggered this | Groups events per request |
| phi_category | Enum | HIPAA category of detected PHI | Same enum as PHIToken.category |
| confidence | Float | Detection confidence | 0.0 - 1.0 |
| action | Enum | What was done | redacted, flagged, passed, blocked |
| detection_method | Enum | How detected | regex, ner, schema, plugin |
| text_length | Integer | Length of original PHI text | For statistics, not the actual text |
| entry_hash | String | SHA-256 hash of this entry's data | For tamper evidence |
| previous_hash | String | Hash of the previous entry | Hash-chain link |

**CRITICAL**: This table NEVER contains original PHI values. Only category, confidence, and metadata.

### ProviderEndpoint

Configuration for an upstream LLM API.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | String | Provider identifier | Primary key: openai, anthropic, google, azure |
| display_name | String | Human-readable name | e.g., "OpenAI GPT-4" |
| base_url | String | Upstream API base URL | e.g., "https://api.openai.com" |
| auth_header | String | Header name for API key | e.g., "Authorization", "x-api-key" |
| auth_prefix | String | Value prefix for API key | e.g., "Bearer ", "" |
| extra_headers | JSON | Additional required headers | e.g., {"anthropic-version": "2023-06-01"} |
| request_format | Enum | API request format | openai_chat, anthropic_messages |
| stream_format | Enum | SSE stream format | openai_sse, anthropic_sse |
| rate_limit_rpm | Integer | Requests per minute limit | Optional, for client-side throttling |
| enabled | Boolean | Whether this provider is active | Default: true |

### Plugin

Registered custom detection/masking plugin.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| name | String | Plugin identifier | Primary key, unique |
| module_path | String | Python module path | e.g., "plugins.custom_mrn" |
| version | String | Plugin version | Semver |
| recognizer_names | List[String] | Recognizers this plugin registers | e.g., ["CustomMRNRecognizer"] |
| masker_names | List[String] | Maskers this plugin registers | e.g., ["CustomMRNMasker"] |
| enabled | Boolean | Whether plugin is active | Default: true |
| load_error | String | Last load error message | Nullable |
| loaded_at | DateTime | When plugin was last loaded | UTC |

### ComplianceReport

Generated compliance evidence document.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | UUID | Report identifier | Primary key |
| generated_at | DateTime | Report generation timestamp | UTC |
| report_type | Enum | Type of report | safe_harbor, audit_summary, session_detail |
| time_range_start | DateTime | Report period start | UTC |
| time_range_end | DateTime | Report period end | UTC |
| total_requests | Integer | Total proxy requests in period | >= 0 |
| total_redactions | Integer | Total PHI redactions in period | >= 0 |
| redactions_by_category | JSON | Breakdown by HIPAA category | {"PERSON_NAME": 150, "SSN": 23, ...} |
| confidence_distribution | JSON | Confidence score histogram | {"0.9-1.0": 450, "0.8-0.9": 30, ...} |
| methodology | String | De-identification methodology description | Safe Harbor method text |
| output_format | Enum | Report file format | markdown, html, pdf |
| output_path | String | File path of generated report | Absolute path |

## Validation Rules

1. **VaultEntry.original_encrypted** is NEVER stored in plaintext. Fernet encryption is mandatory.
2. **RedactionEvent** NEVER contains original PHI text — only category, confidence, and metadata.
3. **Session.date_shift_offset_days** is set once at session creation and immutable for the session lifetime.
4. **VaultEntry deduplication**: Same `(session_id, original_hash)` reuses the existing synthetic value (consistency guarantee).
5. **Hash chain integrity**: `RedactionEvent.entry_hash = SHA256(timestamp + session_id + category + confidence + action + previous_hash)`.
6. **Session isolation**: Vault queries MUST always filter by session_id. Cross-session access is forbidden at the query layer.
