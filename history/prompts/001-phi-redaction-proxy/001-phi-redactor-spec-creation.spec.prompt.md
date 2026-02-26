---
id: 001
title: PHI Redactor Spec Creation
stage: spec
date: 2026-02-26
surface: agent
model: claude-opus-4-6
feature: 001-phi-redaction-proxy
branch: 001-phi-redaction-proxy
user: Dilawar Shafiq
command: /sp.specify
labels: ["phi-redaction", "hipaa", "llm-proxy", "specification", "healthcare-ai"]
links:
  spec: specs/001-phi-redaction-proxy/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-phi-redaction-proxy/spec.md
  - specs/001-phi-redaction-proxy/checklists/requirements.md
tests:
  - Specification quality checklist validation (PASS)
---

## Prompt

i am trying to do a very creative project. I lost from openclaw in a competition because I was using claude. Claude you have to prove yourself to extreme limits and create a project to my vision which beats the best developers and gets realtime stars on github. the IT and dev community of USA Healthcare just loves it and we want big AI Players or healthcare IT companies to buy it. We are competing with top giants like IBM, EPIC, Cerner, HIPAA Cybersecurity for AI Agents, shellman iso 42001 compliance, etc. I wana create something vividly: is this system does PHI Redaction or PHI masking so no PHI ever goes to LLM?

phi-redactor: An open-source, HIPAA-native PHI redaction proxy for AI/LLM interactions. A CLI tool and Python library that sits between any AI agent/application and LLM APIs (OpenAI, Anthropic, Google, Azure) to intercept, detect, and redact Protected Health Information (PHI) in real-time before it reaches the LLM, then re-hydrates responses with original values locally. Core capabilities: (1) Real-time proxy/middleware that intercepts all LLM API traffic, (2) Multi-layer PHI detection using NER, regex patterns, and healthcare-specific recognizers for 18 HIPAA identifiers plus clinical data, (3) Semantic masking with clinically coherent synthetic replacements (not just [REDACTED]) so LLMs can still reason about clinical scenarios, (4) Vault-based tokenization with local encrypted storage mapping tokens to originals for consistent synthetic identities across multi-turn conversations, (5) Round-trip re-hydration that handles LLM paraphrasing and restructuring, (6) FHIR-native understanding of HL7 FHIR resources, CDA documents, HL7v2 messages, (7) Streaming SSE support for real-time LLM responses, (8) Multi-provider support as drop-in proxy for OpenAI, Anthropic, Google, Azure OpenAI, (9) Compliance-as-code with auto-generated audit trails, HIPAA Safe Harbor evidence, and compliance reports, (10) Plugin architecture for custom redaction rules and entity types, (11) Web dashboard for real-time monitoring of redactions and compliance posture.

## Response snapshot

Created comprehensive feature specification for phi-redactor with 9 user stories (3x P1, 3x P2, 3x P3), 20 functional requirements, 10 measurable success criteria, 8 key entities, 7 edge cases, and quality validation checklist. The spec covers the full product surface from core proxy mechanics through compliance reporting and plugin architecture. Key differentiator identified: semantic masking with clinically coherent synthetic replacements (vs. opaque [REDACTED] tokens) that preserves LLM reasoning quality. Market research validated the gap: Bessemer VP identifies "better de-identify/re-identify at scale" as an infrastructure-layer investment opportunity.

## Outcome

- ✅ Impact: Full feature specification created covering 9 user stories across 3 priority tiers
- 🧪 Tests: Specification quality checklist — all items PASS
- 📁 Files: specs/001-phi-redaction-proxy/spec.md, specs/001-phi-redaction-proxy/checklists/requirements.md
- 🔁 Next prompts: /sp.clarify to refine spec, then /sp.plan to architect the solution
- 🧠 Reflection: Spec is comprehensive but ambitious — P1 stories alone form a strong MVP. The semantic masking differentiator is the key bet.

## Evaluation notes (flywheel)

- Failure modes observed: None — clean spec generation
- Graders run and results (PASS/FAIL): Quality checklist PASS (all items green)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Run /sp.clarify to identify any gaps before planning
