"""
tests/test_models.py
Tests that all Pydantic models validate correctly.
Run with: pytest tests/
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from models import ExtractedFields, PADecision, PAStatus, AppealLetter, ClinicalNote


def test_extracted_fields_valid():
    f = ExtractedFields(
        patient_id="PT-001",
        patient_age=55,
        diagnosis_codes=["M16.11"],
        procedure_codes=["27447"],
        clinical_justification="Patient has severe osteoarthritis unresponsive to conservative therapy.",
        ordering_provider="Dr. Smith",
        payer="UnitedHealthcare",
        urgency="routine"
    )
    assert f.patient_id == "PT-001"
    assert f.patient_age == 55
    assert "M16.11" in f.diagnosis_codes


def test_extracted_fields_optional_age():
    f = ExtractedFields(
        patient_id="PT-002",
        patient_age=None,
        diagnosis_codes=["I25.10"],
        procedure_codes=["93306"],
        clinical_justification="Cardiac evaluation required.",
        ordering_provider="Dr. Lee",
        payer="Aetna",
        urgency="urgent"
    )
    assert f.patient_age is None


def test_pa_decision_approved():
    d = PADecision(
        case_id="CASE001",
        status=PAStatus.APPROVED,
        confidence_score=0.85,
        reason="All criteria met.",
        missing_criteria=[],
        recommended_action="Proceed with scheduling."
    )
    assert d.status == PAStatus.APPROVED
    assert d.confidence_score == 0.85


def test_pa_decision_denied():
    d = PADecision(
        case_id="CASE002",
        status=PAStatus.DENIED,
        confidence_score=0.35,
        reason="Procedure not covered.",
        missing_criteria=["Procedure not in approved list"],
        recommended_action="Submit appeal."
    )
    assert d.status == PAStatus.DENIED
    assert len(d.missing_criteria) == 1


def test_appeal_letter():
    a = AppealLetter(
        case_id="CASE002",
        denial_reason="Procedure not covered.",
        letter_text="Dear UnitedHealthcare, we appeal this decision...",
        evidence_cited=["M16.11", "27447"]
    )
    assert a.case_id == "CASE002"
    assert "appeal" in a.letter_text.lower()


def test_clinical_note():
    n = ClinicalNote(raw_text="Patient presents with knee pain.", source_file="test.pdf")
    assert n.source_file == "test.pdf"
