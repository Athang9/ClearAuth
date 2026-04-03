"""
tests/test_pa_engine.py
Tests the PA decision engine without needing the API.
Run with: python -m pytest tests/ -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models import ExtractedFields, PAStatus
from pa_engine import evaluate_pa, load_policy


def make_fields(**overrides):
    """Helper — create a valid ExtractedFields with sensible defaults."""
    defaults = dict(
        patient_id="PT-TEST",
        patient_age=55,
        diagnosis_codes=["M16.11"],
        procedure_codes=["27447"],
        clinical_justification=(
            "Patient has severe end-stage osteoarthritis of the right knee with complete "
            "loss of joint space on weight-bearing X-ray. Conservative management including "
            "18 months of physical therapy, NSAIDs, and two corticosteroid injections has "
            "failed to provide adequate relief. Total knee replacement is medically necessary."
        ),
        ordering_provider="Dr. Test",
        payer="UnitedHealthcare",
        urgency="urgent",  # urgent gives +0.1 uplift → 0.8 → APPROVED
    )
    defaults.update(overrides)
    return ExtractedFields(**defaults)


def test_approved_case():
    """A well-documented urgent case with matching codes should be approved."""
    fields = make_fields()
    decision = evaluate_pa(fields)
    assert decision.status == PAStatus.APPROVED, (
        f"Expected APPROVED but got {decision.status.value} "
        f"(confidence={decision.confidence_score})"
    )
    assert decision.confidence_score >= 0.75
    assert decision.case_id != ""


def test_denied_case_wrong_procedure():
    """A procedure not in the payer's list should lower the score toward denial."""
    fields = make_fields(procedure_codes=["99999"], urgency="routine")
    decision = evaluate_pa(fields)
    assert decision.confidence_score < 0.75
    assert any("procedure" in m.lower() for m in decision.missing_criteria)


def test_urgent_case_gets_uplift():
    """Urgent cases should score higher than routine."""
    routine = evaluate_pa(make_fields(urgency="routine"))
    urgent = evaluate_pa(make_fields(urgency="urgent"))
    assert urgent.confidence_score >= routine.confidence_score


def test_emergent_case_gets_uplift():
    """Emergent cases should score higher than routine."""
    routine = evaluate_pa(make_fields(urgency="routine"))
    emergent = evaluate_pa(make_fields(urgency="emergent"))
    assert emergent.confidence_score >= routine.confidence_score


def test_short_justification_penalised():
    """Very short clinical justification should reduce the score."""
    short = make_fields(clinical_justification="Knee hurts.")
    normal = make_fields()
    assert (
        evaluate_pa(short).confidence_score
        < evaluate_pa(normal).confidence_score
    )


def test_decision_has_recommended_action():
    """Every decision must include a recommended next action."""
    decision = evaluate_pa(make_fields())
    assert len(decision.recommended_action) > 0


def test_confidence_in_valid_range():
    """Confidence score must always be between 0.0 and 1.0 inclusive."""
    for urgency in ("routine", "urgent", "emergent"):
        decision = evaluate_pa(make_fields(urgency=urgency))
        assert 0.0 <= decision.confidence_score <= 1.0


def test_load_policy_uhc():
    """UHC policy file should load and contain expected structure."""
    policy = load_policy("UnitedHealthcare")
    assert "approved_procedures" in policy
    assert isinstance(policy["approved_procedures"], list)
    assert len(policy["approved_procedures"]) > 0


def test_load_policy_fallback():
    """Unknown payer should return a safe generic fallback policy."""
    policy = load_policy("SomeCompletelyUnknownInsurer")
    assert "approved_procedures" in policy
    assert isinstance(policy["approved_procedures"], list)


def test_denied_case_has_missing_criteria():
    """A denied case must list what criteria were missing."""
    fields = make_fields(
        procedure_codes=["99999"],
        diagnosis_codes=["Z99.99"],
        urgency="routine",
    )
    decision = evaluate_pa(fields)
    if decision.status == PAStatus.DENIED:
        assert len(decision.missing_criteria) > 0


def test_denied_returns_appeal_action():
    """A denied case should recommend an appeal action."""
    fields = make_fields(
        procedure_codes=["99999"],
        diagnosis_codes=["Z99.99"],
        urgency="routine",
        clinical_justification="Short.",
    )
    decision = evaluate_pa(fields)
    if decision.status == PAStatus.DENIED:
        assert "appeal" in decision.recommended_action.lower()
