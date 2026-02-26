"""PHI detection engine and recognizer registry.

Public API::

    from phi_redactor.detection import PhiDetectionEngine

    engine = PhiDetectionEngine(sensitivity=0.5)
    detections = engine.detect("Patient John Smith, SSN 123-45-6789")
"""

from __future__ import annotations

from phi_redactor.detection.engine import PhiDetectionEngine

__all__ = ["PhiDetectionEngine"]
