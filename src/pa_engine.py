"""
pa_engine.py
Evaluates a prior authorization request against payer criteria
and returns an approval decision with a confidence score.
"""
import sys
import json
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from models import ExtractedFields, PADecision, PAStatus

_SRC_DIR     = Path(__file__).resolve().parent
POLICIES_DIR = _SRC_DIR.parent / "data" / "payer_policies"


def _payer_matches(payer: str, stem: str) -> bool:
    """
    True when a payer name matches a policy filename stem.
    Handles abbreviations: 'UnitedHealthcare' <-> 'uhc',
    'Aetna' <-> 'aetna', 'Cigna' <-> 'cigna', etc.
    """
    payer_lower = payer.lower()
    stem_lower  = stem.lower()

    # Direct substring match
    if stem_lower in payer_lower or payer_lower in stem_lower:
        return True

    # Abbreviation: initials of each word in the payer name
    words    = payer_lower.replace("-", " ").split()
    initials = "".join(w[0] for w in words if w)
    if stem_lower == initials:
        return True

    # Any individual word in the payer name matches the stem
    if any(w == stem_lower for w in words):
        return True

    return False


def load_policy(payer: str) -> dict:
    """Load the payer's policy JSON. Falls back to a generic policy if not found."""
    # Search the directory anchored to this file, plus anywhere up the cwd tree
    search_dirs = [POLICIES_DIR]
    for parent in [Path.cwd()] + list(Path.cwd().parents):
        candidate = parent / "data" / "payer_policies"
        if candidate.exists() and candidate not in search_dirs:
            search_dirs.append(candidate)
            break

    for d in search_dirs:
        if not d.exists():
            continue
        for f in d.glob("*.json"):
            if _payer_matches(payer, f.stem):
                with open(f) as fp:
                    return json.load(fp)

    # Generic fallback
    return {
        "approved_procedures": [],
        "required_criteria": {"diagnosis_codes": [], "min_justification_length": 50}
    }


def evaluate_pa(fields: ExtractedFields) -> PADecision:
    """
    Score the PA request against payer policy.
    Returns a PADecision with status, confidence score, and recommended action.
    """
    case_id = str(uuid.uuid4())[:8].upper()
    policy  = load_policy(fields.payer)

    approved_procs    = policy.get("approved_procedures", [])
    required_criteria = policy.get("required_criteria", {})

    missing = []
    score   = 0.2  # baseline

    # 1. Procedure coverage
    matched = [c for c in fields.procedure_codes if c in approved_procs]
    if matched:
        score += 0.2
    else:
        missing.append("Procedure code not found in payer covered benefits list")

    # 2. Diagnosis alignment
    required_dx = required_criteria.get("diagnosis_codes", [])
    if required_dx:
        if any(d in required_dx for d in fields.diagnosis_codes):
            score += 0.2
        else:
            missing.append("Primary diagnosis does not meet payer medical necessity criteria")
    else:
        score += 0.1  # no specific dx requirement = slight uplift

    # 3. Urgency uplift
    if fields.urgency in ("urgent", "emergent"):
        score += 0.1

    # 4. Documentation quality
    min_len = required_criteria.get("min_justification_length", 50)
    if len(fields.clinical_justification) >= min_len:
        score += 0.1
    else:
        missing.append("Clinical justification is insufficient — more detail required")

    score = round(min(score, 1.0), 2)

    if score >= 0.75:
        status = PAStatus.APPROVED
        reason = "All payer criteria satisfied. Procedure is medically necessary and covered."
        action = "Proceed with scheduling. Authorization number will be issued within 24 hours."
    elif score >= 0.5:
        status = PAStatus.PENDING_INFO
        reason = "Partial criteria met. Additional clinical documentation is required."
        action = "Submit supplemental documentation to the payer within 3 business days."
    else:
        status = PAStatus.DENIED
        reason = "Insufficient criteria met. Procedure does not meet payer requirements as submitted."
        action = "Review denial criteria carefully. Consider appeal with peer-to-peer review or additional clinical evidence."

    return PADecision(
        case_id=case_id,
        status=status,
        confidence_score=score,
        reason=reason,
        missing_criteria=missing,
        recommended_action=action
    )
