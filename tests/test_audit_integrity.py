"""Security regression tests for in-memory audit integrity."""
from copy import deepcopy

import pytest

from agents.base import AuditTrail, PHIGuard, SecurityException


def test_hmac_detects_modified_fields():
    audit = AuditTrail(secret_key="test-only-secret")
    audit.log("test", "worker", "CALC", {"status": "OK"})
    audit.log("test", "worker", "NEXT", {"status": "OK"})
    assert audit.verify_integrity() is True

    original = deepcopy(audit.logs)
    audit.logs[0]["event_type"] = "MODIFIED"
    assert audit.verify_integrity() is False
    audit.logs = deepcopy(original)

    audit.logs[-1]["current_hash"] = "0" * 64
    assert audit.verify_integrity() is False


def test_trail_returns_defensive_copies():
    audit = AuditTrail(secret_key="test-only-secret")
    audit.log("test", "worker", "CALC", {"status": "OK"})
    extracted = audit.get_trail()
    extracted[0]["actor"] = "tampered"
    assert audit.verify_integrity() is True
    assert audit.get_trail()[0]["actor"] == "test"


def test_phi_field_in_audit_event_is_rejected():
    audit = AuditTrail(secret_key="test-only-secret")
    with pytest.raises(SecurityException):
        audit.log("John Doe", "worker", "CALC", {"status": "OK"})
    assert audit.get_trail() == []
