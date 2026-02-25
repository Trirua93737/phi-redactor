---
id: 002
title: LLM API Proxy Architecture Research
stage: general
date: 2026-02-26
surface: agent
model: claude-opus-4-6
feature: 001-phi-redaction-proxy
branch: master
user: TechTiesIbrahim
command: research
labels: ["fastapi", "openai-api", "anthropic-api", "sse-streaming", "reverse-proxy", "session-management", "phi-redaction"]
links:
  spec: specs/001-phi-redaction-proxy/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - history/prompts/001-phi-redaction-proxy/002-llm-api-proxy-architecture-research.general.prompt.md
tests:
  - N/A (research only, no code produced)
---

## Prompt

Research task for phi-redactor project architecture. Do NOT write any code. Research only.

I need detailed technical findings on building an LLM API proxy:

1. **FastAPI as a reverse proxy for LLM APIs**:
   - Best patterns for building an async reverse proxy with FastAPI
   - How to transparently proxy OpenAI API requests (chat completions, embeddings)
   - How to handle SSE (Server-Sent Events) streaming through a FastAPI proxy
   - How httpx AsyncClient works for forwarding requests to upstream LLM APIs
   - Middleware patterns for request/response interception in FastAPI

2. **OpenAI API contract**:
   - Chat completions endpoint: request/response schema
   - Streaming (SSE) response format — how tokens arrive in chunks
   - Embeddings endpoint schema
   - Authentication (API key forwarding)
   - How base_url works in the OpenAI Python SDK for proxy redirection

3. **Anthropic API contract**:
   - Messages endpoint: request/response schema
   - Streaming response format differences from OpenAI
   - Authentication pattern
   - How base_url works in the Anthropic Python SDK

4. **SSE streaming re-hydration challenge**:
   - When tokens arrive in chunks (e.g., "Sar" then "ah" then " Ch" then "en"), how do you detect and re-hydrate a synthetic name that's split across chunks?
   - Buffer strategies for streaming token re-assembly
   - Maintaining streaming latency while doing token matching

5. **Session management for multi-turn conversations**:
   - How to identify and track sessions across multiple API calls
   - Session ID strategies (header-based, cookie-based, conversation-ID-based)
   - Session timeout and cleanup patterns

Return detailed findings with specific API schemas, architecture patterns, and recommendations.

## Response snapshot

Comprehensive research delivered across 5 domains:

1. **FastAPI reverse proxy**: httpx.AsyncClient with lifespan init, StreamingResponse with aiter_lines() for SSE interception, route-level handlers preferred over middleware for transformation logic. fastapi-proxy-lib as reference architecture.

2. **OpenAI API contract**: Full request/response schemas for /v1/chat/completions (required: model, messages; streaming via data: JSON lines terminated by data: [DONE]) and /v1/embeddings (non-streaming). base_url parameter or OPENAI_BASE_URL env var for SDK redirection.

3. **Anthropic API contract**: /v1/messages endpoint with x-api-key + anthropic-version headers, max_tokens required, system prompt as top-level field. Streaming uses named SSE events (message_start, content_block_delta, message_delta, message_stop) — fundamentally different from OpenAI's format. base_url or ANTHROPIC_BASE_URL for SDK redirection.

4. **SSE streaming re-hydration**: Sliding window buffer (3-5 tokens) with delayed emission for PHI detection across chunk boundaries. Entity-aware trie as advanced alternative. LiteLLM+Presidio reference implementation has streaming limitations — this is a differentiator opportunity.

5. **Session management**: X-Session-ID custom header recommended, with conversation-hash fallback. 30-min idle timeout, in-memory store for single instance, Redis for multi-instance. Session holds PHI entity registry across turns.

## Outcome

- Impact: Established technical foundation for proxy architecture decisions covering both API providers, streaming challenges, and session state management.
- Tests: N/A (research only)
- Files: PHR created
- Next prompts: Create architectural plan incorporating these findings; define task breakdown for proxy implementation; decide on PHI detection strategy (regex vs NER vs trie).
- Reflection: The SSE streaming chunk boundary problem is the most technically challenging aspect. LiteLLM's approach with Presidio does not fully solve it for streaming — this validates the need for a custom buffer-based solution. OpenAI and Anthropic have fundamentally different streaming formats requiring separate parser implementations.

## Evaluation notes (flywheel)

- Failure modes observed: WebFetch tool was unavailable, limiting ability to extract complete API schemas directly from documentation pages. Compensated with multiple targeted web searches.
- Graders run and results (PASS/FAIL): N/A (research task)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Validate streaming buffer approach with a minimal prototype against actual OpenAI streaming output.
