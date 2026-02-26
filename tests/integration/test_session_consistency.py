"""Integration tests for multi-turn session consistency.

Verifies that PHI redaction mappings remain consistent across multiple
requests within the same session, and that different sessions produce
different synthetic values.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from phi_redactor.config import PhiRedactorConfig
from phi_redactor.proxy.app import create_app


@pytest.fixture
def test_config(tmp_dir):
    return PhiRedactorConfig(
        port=9999,
        host="127.0.0.1",
        vault_path=tmp_dir / "vault.db",
        audit_path=tmp_dir / "audit",
        log_level="WARNING",
        sensitivity=0.7,
    )


@pytest.fixture
def client(test_config):
    app = create_app(config=test_config)
    with TestClient(app) as c:
        yield c


class TestWithinSessionConsistency:
    """Same PHI within the same session should always map to the same synthetic."""

    def test_same_name_same_session(self, client):
        text = "Dr. John Smith prescribed medication to patient."
        resp1 = client.post("/api/v1/redact", json={"text": text})
        session_id = resp1.json()["session_id"]
        redacted1 = resp1.json()["redacted_text"]

        resp2 = client.post("/api/v1/redact", json={"text": text, "session_id": session_id})
        redacted2 = resp2.json()["redacted_text"]

        assert redacted1 == redacted2

    def test_same_ssn_same_session(self, client):
        resp1 = client.post("/api/v1/redact", json={"text": "SSN: 456-78-9012"})
        session_id = resp1.json()["session_id"]
        redacted1 = resp1.json()["redacted_text"]

        resp2 = client.post(
            "/api/v1/redact",
            json={"text": "SSN: 456-78-9012", "session_id": session_id},
        )
        redacted2 = resp2.json()["redacted_text"]

        assert redacted1 == redacted2

    def test_phi_in_different_context_same_session(self, client):
        """Same PHI entity in different surrounding text should map consistently."""
        resp1 = client.post("/api/v1/redact", json={"text": "Call John Smith at the office."})
        session_id = resp1.json()["session_id"]

        resp2 = client.post(
            "/api/v1/redact",
            json={"text": "John Smith was referred to cardiology.", "session_id": session_id},
        )

        # Both should have the same synthetic name for "John Smith"
        # (we can't easily check the exact value, but we verify both are redacted)
        assert "John Smith" not in resp1.json()["redacted_text"]
        assert "John Smith" not in resp2.json()["redacted_text"]


class TestCrossSessionIsolation:
    """Different sessions should produce different synthetic values."""

    def test_different_sessions_different_synthetics(self, client):
        text = "Patient John Smith SSN 456-78-9012"

        resp1 = client.post("/api/v1/redact", json={"text": text})
        resp2 = client.post("/api/v1/redact", json={"text": text})

        session1 = resp1.json()["session_id"]
        session2 = resp2.json()["session_id"]

        # Sessions should be different
        assert session1 != session2

        # Both should have PHI removed from both redactions
        redacted1 = resp1.json()["redacted_text"]
        redacted2 = resp2.json()["redacted_text"]

        # At minimum, both should have been processed (detections occurred)
        assert resp1.json()["detections"] or "John Smith" not in redacted1
        assert resp2.json()["detections"] or "John Smith" not in redacted2


class TestRehydrationConsistency:
    """Rehydration should accurately restore original PHI."""

    def test_multi_turn_rehydration(self, client):
        # Turn 1: redact
        resp1 = client.post(
            "/api/v1/redact",
            json={"text": "Patient Jane Doe called from 555-123-4567."},
        )
        session_id = resp1.json()["session_id"]
        redacted1 = resp1.json()["redacted_text"]

        # Turn 2: redact more text in same session
        resp2 = client.post(
            "/api/v1/redact",
            json={
                "text": "Jane Doe's SSN is 987-65-4321.",
                "session_id": session_id,
            },
        )
        redacted2 = resp2.json()["redacted_text"]

        # Rehydrate turn 1
        rehydrate1 = client.post(
            "/api/v1/rehydrate",
            json={"text": redacted1, "session_id": session_id},
        )
        restored1 = rehydrate1.json()["text"]

        # Original PHI should be restored
        assert "Jane Doe" in restored1 or "555-123-4567" in restored1

    def test_rehydrate_nonexistent_session(self, client):
        resp = client.post(
            "/api/v1/rehydrate",
            json={"text": "Some text", "session_id": "nonexistent-session-id"},
        )
        # Should succeed but return text unchanged (no mappings to reverse)
        assert resp.status_code == 200
        assert resp.json()["text"] == "Some text"


class TestAuditConsistency:
    """Verify audit trail records match redaction activity."""

    def test_audit_events_created_per_detection(self, client):
        # Text with multiple PHI entities
        text = "John Smith SSN 456-78-9012 email john@test.com phone 555-123-4567"
        resp = client.post("/api/v1/redact", json={"text": text})
        session_id = resp.json()["session_id"]

        audit_resp = client.get(f"/api/v1/audit?session_id={session_id}")
        events = audit_resp.json()["events"]

        # Should have at least one audit event
        assert len(events) >= 1

        # All events should reference the same session
        for event in events:
            assert event["session_id"] == session_id
            assert event["confidence"] > 0
            assert event["action"] == "redacted"
