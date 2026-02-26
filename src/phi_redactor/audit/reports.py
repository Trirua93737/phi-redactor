"""HIPAA Safe Harbor compliance report generator.

Produces structured evidence reports that demonstrate de-identification
compliance with the HIPAA Safe Harbor method (45 CFR 164.514(b)(2)).
Reports can be used for:

- Internal compliance audits
- External regulatory reviews
- Breach risk assessments
- Continuous monitoring dashboards
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phi_redactor.audit.trail import AuditTrail
from phi_redactor.models import AuditEvent, PHICategory

# All 18 HIPAA Safe Harbor identifier categories
_SAFE_HARBOR_CATEGORIES = [cat.value for cat in PHICategory]


class ComplianceReportGenerator:
    """Generates HIPAA Safe Harbor compliance evidence reports.

    Parameters
    ----------
    audit_trail:
        The :class:`AuditTrail` instance to query for redaction events.
    """

    def __init__(self, audit_trail: AuditTrail) -> None:
        self._audit = audit_trail

    def generate_report(
        self,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate a full compliance report.

        Args:
            from_dt: Inclusive start of the reporting period (UTC).
            to_dt: Inclusive end of the reporting period (UTC).
            session_id: Optional filter to a specific session.

        Returns:
            A structured dict containing the full compliance report.
        """
        now = datetime.now(timezone.utc)
        events = self._audit.query(
            session_id=session_id,
            from_dt=from_dt,
            to_dt=to_dt,
            limit=100_000,
        )

        return {
            "report_metadata": {
                "title": "HIPAA Safe Harbor De-identification Compliance Report",
                "generated_at": now.isoformat(),
                "reporting_period": {
                    "from": from_dt.isoformat() if from_dt else "inception",
                    "to": to_dt.isoformat() if to_dt else now.isoformat(),
                },
                "session_filter": session_id,
                "standard": "45 CFR 164.514(b)(2) - Safe Harbor Method",
            },
            "summary": self._build_summary(events),
            "category_coverage": self._build_category_coverage(events),
            "confidence_analysis": self._build_confidence_analysis(events),
            "detection_methods": self._build_detection_methods(events),
            "integrity_verification": self._verify_integrity(),
            "compliance_status": self._assess_compliance(events),
        }

    def generate_summary(
        self,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> dict[str, Any]:
        """Generate a lightweight summary report.

        Suitable for dashboards and quick status checks.
        """
        events = self._audit.query(from_dt=from_dt, to_dt=to_dt, limit=100_000)
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            **self._build_summary(events),
            "compliance_status": self._assess_compliance(events),
        }

    def export_report(
        self,
        output_path: str | Path,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
        session_id: str | None = None,
    ) -> Path:
        """Generate and write the full report as a JSON file.

        Returns the path to the written file.
        """
        report = self.generate_report(
            from_dt=from_dt, to_dt=to_dt, session_id=session_id,
        )
        path = Path(output_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    # Report sections
    # ------------------------------------------------------------------

    @staticmethod
    def _build_summary(events: list[AuditEvent]) -> dict[str, Any]:
        """High-level statistics."""
        if not events:
            return {
                "total_redaction_events": 0,
                "unique_sessions": 0,
                "unique_requests": 0,
                "phi_entities_detected": 0,
                "categories_detected": 0,
            }

        sessions = {e.session_id for e in events}
        requests = {e.request_id for e in events}
        categories = {e.phi_category.value for e in events}

        return {
            "total_redaction_events": len(events),
            "unique_sessions": len(sessions),
            "unique_requests": len(requests),
            "phi_entities_detected": len(events),
            "categories_detected": len(categories),
        }

    def _build_category_coverage(self, events: list[AuditEvent]) -> dict[str, Any]:
        """Show which of the 18 HIPAA categories were detected and redacted."""
        detected = Counter(e.phi_category.value for e in events)

        coverage = {}
        for cat in _SAFE_HARBOR_CATEGORIES:
            count = detected.get(cat, 0)
            coverage[cat] = {
                "detected_count": count,
                "status": "covered" if count > 0 else "not_observed",
            }

        covered_count = sum(1 for c in coverage.values() if c["status"] == "covered")

        return {
            "total_categories": len(_SAFE_HARBOR_CATEGORIES),
            "categories_covered": covered_count,
            "coverage_percentage": round(covered_count / len(_SAFE_HARBOR_CATEGORIES) * 100, 1),
            "categories": coverage,
        }

    @staticmethod
    def _build_confidence_analysis(events: list[AuditEvent]) -> dict[str, Any]:
        """Analyze detection confidence distribution."""
        if not events:
            return {
                "average_confidence": 0.0,
                "min_confidence": 0.0,
                "max_confidence": 0.0,
                "distribution": {},
            }

        confidences = [e.confidence for e in events]
        avg = sum(confidences) / len(confidences)

        # Bucket into ranges
        buckets = {"0.0-0.5": 0, "0.5-0.7": 0, "0.7-0.9": 0, "0.9-1.0": 0}
        for c in confidences:
            if c < 0.5:
                buckets["0.0-0.5"] += 1
            elif c < 0.7:
                buckets["0.5-0.7"] += 1
            elif c < 0.9:
                buckets["0.7-0.9"] += 1
            else:
                buckets["0.9-1.0"] += 1

        return {
            "average_confidence": round(avg, 4),
            "min_confidence": round(min(confidences), 4),
            "max_confidence": round(max(confidences), 4),
            "distribution": buckets,
        }

    @staticmethod
    def _build_detection_methods(events: list[AuditEvent]) -> dict[str, int]:
        """Count events by detection method."""
        return dict(Counter(e.detection_method.value for e in events))

    def _verify_integrity(self) -> dict[str, Any]:
        """Verify audit trail hash-chain integrity."""
        is_valid = self._audit.verify_integrity()
        return {
            "hash_chain_valid": is_valid,
            "status": "passed" if is_valid else "FAILED",
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _assess_compliance(events: list[AuditEvent]) -> dict[str, Any]:
        """Assess overall compliance status based on evidence."""
        if not events:
            return {
                "overall": "no_data",
                "message": "No redaction events found in the reporting period.",
                "checks": {},
            }

        checks: dict[str, dict[str, Any]] = {}

        # Check 1: All detections were redacted
        redacted = sum(1 for e in events if e.action.value == "redacted")
        checks["all_detections_redacted"] = {
            "passed": redacted == len(events),
            "detail": f"{redacted}/{len(events)} detections were redacted",
        }

        # Check 2: Confidence threshold
        low_confidence = sum(1 for e in events if e.confidence < 0.3)
        checks["confidence_threshold"] = {
            "passed": low_confidence == 0,
            "detail": f"{low_confidence} detections below 0.3 confidence threshold",
        }

        # Check 3: Multiple detection methods used
        methods = {e.detection_method.value for e in events}
        checks["multiple_detection_methods"] = {
            "passed": len(methods) >= 2,
            "detail": f"Used {len(methods)} detection method(s): {', '.join(sorted(methods))}",
        }

        # Check 4: Multiple PHI categories handled
        categories = {e.phi_category.value for e in events}
        checks["multi_category_coverage"] = {
            "passed": len(categories) >= 3,
            "detail": f"Covered {len(categories)} PHI categories",
        }

        all_passed = all(c["passed"] for c in checks.values())

        return {
            "overall": "compliant" if all_passed else "review_needed",
            "message": (
                "All compliance checks passed."
                if all_passed
                else "Some checks require review. See details."
            ),
            "checks": checks,
        }
