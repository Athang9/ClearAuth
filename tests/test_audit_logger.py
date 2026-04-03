"""
tests/test_audit_logger.py
Tests the audit logger writes and reads correctly.
Run with: pytest tests/
"""
import sys
import sqlite3
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import audit_logger


def test_log_and_read(tmp_path, monkeypatch):
    """Audit log should write a row and read it back correctly."""
    monkeypatch.setattr(audit_logger, "DB_PATH", tmp_path / "test_audit.db")

    audit_logger.log_event(
        case_id="TEST001",
        action="pa_decision",
        payer="Aetna",
        status="approved",
        confidence=0.82,
        details={"note": "test"}
    )

    events = audit_logger.get_all_events()
    assert len(events) == 1
    assert events[0]["case_id"] == "TEST001"
    assert events[0]["action"] == "pa_decision"
    assert events[0]["status"] == "approved"
    assert events[0]["confidence"] == 0.82


def test_multiple_events(tmp_path, monkeypatch):
    """Multiple log events should all be stored."""
    monkeypatch.setattr(audit_logger, "DB_PATH", tmp_path / "test_audit2.db")

    audit_logger.log_event("C001", "document_intake", payer="UHC")
    audit_logger.log_event("C001", "pa_decision", payer="UHC", status="denied", confidence=0.3)
    audit_logger.log_event("C001", "appeal_generated", payer="UHC")

    events = audit_logger.get_all_events()
    assert len(events) == 3
    actions = [e["action"] for e in events]
    assert "document_intake"  in actions
    assert "pa_decision"      in actions
    assert "appeal_generated" in actions


def test_no_phi_in_log(tmp_path, monkeypatch):
    """Log must not contain patient names or clinical notes."""
    monkeypatch.setattr(audit_logger, "DB_PATH", tmp_path / "test_audit3.db")

    audit_logger.log_event(
        case_id="C002",
        action="pa_decision",
        payer="Cigna",
        status="approved",
        confidence=0.78,
        details={}
    )

    conn = sqlite3.connect(tmp_path / "test_audit3.db")
    rows = conn.execute("SELECT * FROM audit_log").fetchall()
    conn.close()

    full_text = str(rows).lower()
    # These PHI fields should never appear in the log
    for phi_field in ["patient_name", "date_of_birth", "address", "clinical_note"]:
        assert phi_field not in full_text
