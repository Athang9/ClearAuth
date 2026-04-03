"""
pipeline.py
Full end-to-end prior authorization pipeline.
Usage: python pipeline.py <path_to_pdf>
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from document_intake import intake_pdf
from pa_engine import evaluate_pa
from appeals_generator import generate_appeal
from audit_logger import log_event

OUTPUT_DIR = Path(__file__).parent.parent / "outputs"


def run_pipeline(pdf_path: str) -> dict:
    """
    Run the full ClearAuth pipeline on a single clinical note PDF.
    Returns a summary dict with decision and paths to outputs.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "appeal_letters").mkdir(exist_ok=True)

    print("\n" + "=" * 55)
    print("  ClearAuth — Prior Authorization Pipeline")
    print("=" * 55)

    # ── STEP 1: Document Intake ──────────────────────────────
    print("\n[Step 1/3] Document Intake")
    print("  Extracting structured fields from PDF...")
    fields = intake_pdf(pdf_path)
    print(f"  Patient ID   : {fields.patient_id}")
    print(f"  Diagnoses    : {', '.join(fields.diagnosis_codes)}")
    print(f"  Procedures   : {', '.join(fields.procedure_codes)}")
    print(f"  Payer        : {fields.payer}")
    print(f"  Urgency      : {fields.urgency}")

    log_event(
        case_id="PENDING",
        action="document_intake",
        payer=fields.payer,
        details={"source_file": pdf_path}
    )

    # ── STEP 2: PA Decision ──────────────────────────────────
    print("\n[Step 2/3] Prior Authorization Decision")
    decision = evaluate_pa(fields)
    status_display = {
        "approved": "APPROVED",
        "denied": "DENIED",
        "pending_info": "PENDING — MORE INFO NEEDED"
    }
    print(f"  Case ID      : {decision.case_id}")
    print(f"  Status       : {status_display[decision.status.value]}")
    print(f"  Confidence   : {decision.confidence_score:.0%}")
    print(f"  Reason       : {decision.reason}")
    if decision.missing_criteria:
        print(f"  Missing      : {'; '.join(decision.missing_criteria)}")
    print(f"  Next Step    : {decision.recommended_action}")

    log_event(
        case_id=decision.case_id,
        action="pa_decision",
        payer=fields.payer,
        status=decision.status.value,
        confidence=decision.confidence_score
    )

    # ── STEP 3: Appeals (only if denied) ────────────────────
    appeal_path = None
    if decision.status.value == "denied":
        print("\n[Step 3/3] Generating Appeal Letter")
        print("  Drafting appeal with clinical evidence...")
        appeal = generate_appeal(decision, fields)
        appeal_path = OUTPUT_DIR / "appeal_letters" / f"{decision.case_id}_appeal.txt"
        appeal_path.write_text(appeal.letter_text, encoding="utf-8")
        print(f"  Appeal letter saved to: {appeal_path}")

        log_event(
            case_id=decision.case_id,
            action="appeal_generated",
            payer=fields.payer
        )
    else:
        print(f"\n[Step 3/3] No appeal needed — status is {decision.status.value}")

    print("\n" + "=" * 55)
    print("  Pipeline complete.")
    print("=" * 55 + "\n")

    return {
        "case_id": decision.case_id,
        "status": decision.status.value,
        "confidence": decision.confidence_score,
        "appeal_letter": str(appeal_path) if appeal_path else None
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <path_to_pdf>")
        print("Example: python pipeline.py ../data/synthetic_pdfs/case_001.pdf")
        sys.exit(1)
    result = run_pipeline(sys.argv[1])
    print("Summary:", json.dumps(result, indent=2))
