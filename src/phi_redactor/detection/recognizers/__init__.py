"""Custom HIPAA recognizers for Presidio-based PHI detection.

This package provides 8 custom recognizers that, together with Presidio's
built-in recognizers, cover all 18 HIPAA Safe Harbor identifier categories.

Public API::

    from phi_redactor.detection.recognizers import (
        MRNRecognizer,
        HealthPlanRecognizer,
        AccountRecognizer,
        LicenseRecognizer,
        VehicleRecognizer,
        DeviceRecognizer,
        BiometricRecognizer,
        FaxRecognizer,
    )
"""

from __future__ import annotations

from phi_redactor.detection.recognizers.account import AccountRecognizer
from phi_redactor.detection.recognizers.biometric import BiometricRecognizer
from phi_redactor.detection.recognizers.device import DeviceRecognizer
from phi_redactor.detection.recognizers.fax import FaxRecognizer
from phi_redactor.detection.recognizers.health_plan import HealthPlanRecognizer
from phi_redactor.detection.recognizers.license import LicenseRecognizer
from phi_redactor.detection.recognizers.mrn import MRNRecognizer
from phi_redactor.detection.recognizers.vehicle import VehicleRecognizer

__all__ = [
    "AccountRecognizer",
    "BiometricRecognizer",
    "DeviceRecognizer",
    "FaxRecognizer",
    "HealthPlanRecognizer",
    "LicenseRecognizer",
    "MRNRecognizer",
    "VehicleRecognizer",
]
