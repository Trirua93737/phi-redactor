# Quickstart: phi-redactor

**Branch**: `001-phi-redaction-proxy` | **Date**: 2026-02-26

## Install

```bash
pip install phi-redactor
```

## Start the proxy (one command)

```bash
phi-redactor serve --port 8080
```

On first run, phi-redactor downloads the spaCy English model (~560MB, one-time) and initializes a local encrypted vault.

## Use with OpenAI

```python
from openai import OpenAI

# Just change the base_url — everything else stays the same
client = OpenAI(
    api_key="sk-your-key",
    base_url="http://localhost:8080/openai/v1"
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{
        "role": "user",
        "content": "Summarize the case of John Smith, SSN 123-45-6789, "
                   "67yo male diagnosed with Type 2 Diabetes on 03/15/1998 "
                   "at Springfield General Hospital."
    }]
)

# The LLM never saw "John Smith" or "123-45-6789"
# It received synthetic values like "Sarah Chen" and "987-65-4321"
# But your response contains the originals, fully restored
print(response.choices[0].message.content)
```

## Use with Anthropic

```python
from anthropic import Anthropic

client = Anthropic(
    api_key="sk-ant-your-key",
    base_url="http://localhost:8080/anthropic"
)

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "Review the lab results for Maria Garcia, MRN 00456789..."
    }]
)
print(message.content[0].text)
```

## Use as a Python library (no proxy)

```python
from phi_redactor import PhiRedactor

redactor = PhiRedactor()

# Redact PHI from text
result = redactor.redact(
    "Patient John Smith, DOB 03/15/1956, SSN 123-45-6789, "
    "presented to Springfield General with chest pain."
)

print(result.redacted_text)
# "Patient Sarah Chen, DOB 07/22/1961, SSN 987-65-4321,
#  presented to Riverside Medical with chest pain."

print(result.detections)
# [Detection(category='PERSON_NAME', confidence=0.98, ...),
#  Detection(category='DATE', confidence=0.95, ...),
#  Detection(category='SSN', confidence=0.99, ...),
#  Detection(category='GEOGRAPHIC_DATA', confidence=0.92, ...)]

# Re-hydrate back to originals
original = redactor.rehydrate(result.redacted_text, result.session_id)
print(original)
# "Patient John Smith, DOB 03/15/1956, SSN 123-45-6789,
#  presented to Springfield General with chest pain."
```

## Streaming support

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-your-key",
    base_url="http://localhost:8080/openai/v1"
)

stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Analyze patient records..."}],
    stream=True
)

for chunk in stream:
    # PHI is re-hydrated in real-time as chunks arrive
    print(chunk.choices[0].delta.content, end="", flush=True)
```

## Configuration

```bash
# Environment variables
export PHI_REDACTOR_PORT=8080
export PHI_REDACTOR_DEFAULT_PROVIDER=openai
export PHI_REDACTOR_SENSITIVITY=0.5          # 0.0 (aggressive) to 1.0 (permissive)
export PHI_REDACTOR_VAULT_PATH=~/.phi-redactor/vault.db
export PHI_REDACTOR_AUDIT_PATH=~/.phi-redactor/audit/

# Or use a config file
phi-redactor serve --config ~/.phi-redactor/config.yaml

# Or CLI flags (override everything)
phi-redactor serve --port 9090 --sensitivity 0.3 --provider anthropic
```

Configuration precedence: CLI flags > environment variables > config file > defaults.

## Generate compliance report

```bash
# HIPAA Safe Harbor compliance evidence
phi-redactor report safe-harbor --from 2026-01-01 --to 2026-02-26 --format html

# Audit trail export
phi-redactor audit export --session <session-id> --format json

# Session summary
phi-redactor sessions list
phi-redactor sessions inspect <session-id>
```

## CLI reference

```bash
phi-redactor serve          # Start the proxy server
phi-redactor redact <file>  # Redact PHI from a file (batch mode)
phi-redactor report         # Generate compliance reports
phi-redactor audit          # Query audit trail
phi-redactor sessions       # Manage sessions
phi-redactor config         # Show/edit configuration
phi-redactor plugins        # List/manage plugins
phi-redactor health         # Check proxy health
phi-redactor version        # Show version info
```

## What happens under the hood

```
1. Your app sends a request with PHI
   "John Smith, SSN 123-45-6789, at Springfield General"

2. phi-redactor detects PHI entities
   [PERSON_NAME: "John Smith", SSN: "123-45-6789", GEOGRAPHIC_DATA: "Springfield General"]

3. Semantic masking creates coherent replacements
   "Sarah Chen, SSN 987-65-4321, at Riverside Medical"

4. Mappings stored in encrypted local vault
   {session_abc: {"John Smith" → "Sarah Chen", ...}}

5. Sanitized text sent to LLM
   LLM only sees "Sarah Chen" — never "John Smith"

6. LLM responds with synthetic names
   "Based on Sarah Chen's case..."

7. Re-hydration restores originals
   "Based on John Smith's case..."

8. Audit trail records the redaction event
   {category: "PERSON_NAME", confidence: 0.98, action: "redacted"}
```
