"""
tests/test_model_accuracy.py

Validates the AI extraction model against known ground truth.
For each synthetic PDF, we know EXACTLY what the correct answer is
(stored in data/synthetic_cases/*.json).

We run the model, compare its output to ground truth, and score:
  - Field-level accuracy (did it get each field right?)
  - Hallucination detection (did it invent codes that don't exist?)
  - Overall accuracy score (0-100%)

Run with:
    python tests/test_model_accuracy.py

NOTE: This calls the real Groq API — make sure your .env has GROQ_API_KEY set.
"""
import sys
import json
import time
from pathlib import Path

# Make sure src/ is importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from document_intake import intake_pdf
from models import ExtractedFields

PDF_DIR   = ROOT / "data" / "synthetic_pdfs"
TRUTH_DIR = ROOT / "data" / "synthetic_cases"

# ── Ground truth for all 5 cases ──────────────────────────────────────────────
GROUND_TRUTH = {
    "case_001_PT_10042": {
        "patient_id":        "PT-10042",
        "patient_age":       67,
        "diagnosis_codes":   ["M16.11", "M25.361"],
        "procedure_codes":   ["27447"],
        "payer":             "UnitedHealthcare",
        "urgency":           "routine",
    },
    "case_002_PT_10073": {
        "patient_id":        "PT-10073",
        "patient_age":       54,
        "diagnosis_codes":   ["I25.10", "Z82.49"],
        "procedure_codes":   ["93306"],
        "payer":             "Aetna",
        "urgency":           "urgent",
    },
    "case_003_PT_10091": {
        "patient_id":        "PT-10091",
        "patient_age":       44,
        "diagnosis_codes":   ["K21.0", "K22.70"],
        "procedure_codes":   ["43239"],
        "payer":             "Cigna",
        "urgency":           "urgent",
    },
    "case_004_PT_10108": {
        "patient_id":        "PT-10108",
        "patient_age":       38,
        "diagnosis_codes":   ["M75.1", "M75.121"],
        "procedure_codes":   ["29827"],
        "payer":             "UnitedHealthcare",
        "urgency":           "routine",
    },
    "case_005_PT_10127": {
        "patient_id":        "PT-10127",
        "patient_age":       71,
        "diagnosis_codes":   ["G89.29", "M47.816"],
        "procedure_codes":   ["64483"],
        "payer":             "Aetna",
        "urgency":           "routine",
    },
}

# ── Scoring helpers ────────────────────────────────────────────────────────────

def score_exact(got, expected, field: str) -> tuple[int, int, str]:
    """Returns (points_earned, points_possible, note)"""
    if got == expected:
        return 1, 1, "PASS"
    return 0, 1, f"FAIL  got={got!r}  expected={expected!r}"


def score_codes(got: list, expected: list, field: str) -> tuple[int, int, str]:
    """
    Scores a list of codes:
    - Each correct code = 1 point
    - Each invented code (hallucination) = -1 point (penalty)
    - Missing codes = 0 (no bonus, no penalty)
    Returns (earned, possible, note)
    """
    got_set      = set(c.strip() for c in got)
    expected_set = set(expected)
    correct      = got_set & expected_set
    hallucinated = got_set - expected_set
    missing      = expected_set - got_set

    earned   = len(correct) - len(hallucinated)  # penalty for hallucinations
    possible = len(expected_set)
    earned   = max(earned, 0)  # floor at 0

    parts = []
    if correct:      parts.append(f"correct={sorted(correct)}")
    if hallucinated: parts.append(f"HALLUCINATED={sorted(hallucinated)}")
    if missing:      parts.append(f"missing={sorted(missing)}")
    status = "PASS" if not hallucinated and not missing else ("HALLUCINATION" if hallucinated else "PARTIAL")
    return earned, possible, f"{status}  {' | '.join(parts)}"


def score_payer(got: str, expected: str) -> tuple[int, int, str]:
    """Fuzzy match — UHC / UnitedHealthcare / United Health Care all OK."""
    aliases = {
        "UnitedHealthcare": ["unitedhealthcare", "united healthcare", "uhc", "united health care"],
        "Aetna":            ["aetna"],
        "Cigna":            ["cigna"],
    }
    got_clean = got.lower().strip()
    for canonical, variants in aliases.items():
        if expected == canonical and got_clean in variants:
            return 1, 1, "PASS"
    if got.strip() == expected:
        return 1, 1, "PASS"
    return 0, 1, f"FAIL  got={got!r}  expected={expected!r}"


def score_urgency(got: str, expected: str) -> tuple[int, int, str]:
    if got.lower().strip() == expected.lower().strip():
        return 1, 1, "PASS"
    return 0, 1, f"FAIL  got={got!r}  expected={expected!r}"


def score_age(got, expected) -> tuple[int, int, str]:
    if got == expected:
        return 1, 1, "PASS"
    if got is not None and expected is not None and abs(got - expected) <= 1:
        return 1, 1, f"PASS (off by 1: got {got})"
    return 0, 1, f"FAIL  got={got}  expected={expected}"


# ── Main validation runner ─────────────────────────────────────────────────────

def validate_case(case_name: str, truth: dict) -> dict:
    pdf_path = PDF_DIR / f"{case_name}.pdf"
    if not pdf_path.exists():
        return {"error": f"PDF not found: {pdf_path}"}

    try:
        start   = time.time()
        result  = intake_pdf(str(pdf_path))
        elapsed = round(time.time() - start, 2)
    except Exception as e:
        return {"error": str(e)}

    checks = {}

    # patient_id
    e, p, n = score_exact(result.patient_id, truth["patient_id"], "patient_id")
    checks["patient_id"] = {"earned": e, "possible": p, "note": n}

    # patient_age
    e, p, n = score_age(result.patient_age, truth["patient_age"])
    checks["patient_age"] = {"earned": e, "possible": p, "note": n}

    # diagnosis_codes
    e, p, n = score_codes(result.diagnosis_codes, truth["diagnosis_codes"], "diagnosis_codes")
    checks["diagnosis_codes"] = {"earned": e, "possible": p, "note": n}

    # procedure_codes
    e, p, n = score_codes(result.procedure_codes, truth["procedure_codes"], "procedure_codes")
    checks["procedure_codes"] = {"earned": e, "possible": p, "note": n}

    # payer
    e, p, n = score_payer(result.payer, truth["payer"])
    checks["payer"] = {"earned": e, "possible": p, "note": n}

    # urgency
    e, p, n = score_urgency(result.urgency, truth["urgency"])
    checks["urgency"] = {"earned": e, "possible": p, "note": n}

    total_earned   = sum(c["earned"]   for c in checks.values())
    total_possible = sum(c["possible"] for c in checks.values())
    accuracy       = round(total_earned / total_possible * 100, 1) if total_possible else 0
    hallucinations = sum(
        1 for c in checks.values() if "HALLUCINATION" in c["note"]
    )

    return {
        "case":          case_name,
        "elapsed_sec":   elapsed,
        "checks":        checks,
        "total_earned":  total_earned,
        "total_possible":total_possible,
        "accuracy_pct":  accuracy,
        "hallucinations":hallucinations,
        "extracted":     result.model_dump(),
    }


def bar(pct: float, width: int = 20) -> str:
    filled = int(pct / 100 * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def color_pct(pct: float) -> str:
    if pct >= 90: return f"EXCELLENT ({pct}%)"
    if pct >= 75: return f"GOOD      ({pct}%)"
    if pct >= 50: return f"PARTIAL   ({pct}%)"
    return             f"POOR      ({pct}%)"


def run_validation():
    print("\n" + "=" * 65)
    print("  ClearAuth — Model Accuracy Validation")
    print("  Testing AI extraction against known ground truth")
    print("=" * 65)

    all_results    = []
    total_earned   = 0
    total_possible = 0
    total_halluc   = 0

    for case_name, truth in GROUND_TRUTH.items():
        print(f"\n  Running: {case_name}...")
        res = validate_case(case_name, truth)

        if "error" in res:
            print(f"  ERROR: {res['error']}")
            continue

        all_results.append(res)
        total_earned   += res["total_earned"]
        total_possible += res["total_possible"]
        total_halluc   += res["hallucinations"]

        # Per-case summary
        print(f"  Accuracy : {bar(res['accuracy_pct'])} {color_pct(res['accuracy_pct'])}")
        print(f"  Time     : {res['elapsed_sec']}s")
        print(f"  Fields   :")
        for field, c in res["checks"].items():
            icon = "+" if c["earned"] == c["possible"] else ("!" if "HALLUCINATION" in c["note"] else "x")
            print(f"    [{icon}] {field:<20} {c['note']}")

    # ── Overall report ─────────────────────────────────────────────────────────
    if not all_results:
        print("\n  No results. Check your GROQ_API_KEY and PDF files.")
        return

    overall_pct = round(total_earned / total_possible * 100, 1) if total_possible else 0

    print("\n" + "=" * 65)
    print("  OVERALL RESULTS")
    print("=" * 65)
    print(f"  Cases tested     : {len(all_results)} / {len(GROUND_TRUTH)}")
    print(f"  Overall accuracy : {bar(overall_pct)} {color_pct(overall_pct)}")
    print(f"  Total score      : {total_earned} / {total_possible} fields correct")
    print(f"  Hallucinations   : {total_halluc} (invented codes not in ground truth)")
    print(f"  Avg speed        : {round(sum(r['elapsed_sec'] for r in all_results)/len(all_results),2)}s per case")

    print("\n  Per-case breakdown:")
    print(f"  {'Case':<30} {'Accuracy':>10} {'Halluc':>8} {'Time':>6}")
    print("  " + "-" * 58)
    for r in all_results:
        print(f"  {r['case']:<30} {r['accuracy_pct']:>9}% {r['hallucinations']:>8} {r['elapsed_sec']:>5}s")

    print("\n  What these scores mean:")
    print("  90-100% = Model is highly reliable. Safe for demo.")
    print("  75-89%  = Good but review borderline fields before demo.")
    print("  50-74%  = Partial accuracy. Mention limitations in meeting.")
    print("  <50%    = Check your API key and prompt.")

    # Save JSON report
    report_path = ROOT / "outputs" / "validation_report.json"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w") as f:
        json.dump({
            "overall_accuracy_pct": overall_pct,
            "total_score": f"{total_earned}/{total_possible}",
            "hallucinations": total_halluc,
            "cases": all_results
        }, f, indent=2)
    print(f"\n  Full report saved to: {report_path}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_validation()


# ── Add messy cases to ground truth ──────────────────────────────────────────
GROUND_TRUTH["case_006_PT_10201_messy"] = {
    "patient_id":      "PT-10201",
    "patient_age":     58,
    "diagnosis_codes": ["M54.4", "M47.816"],
    "procedure_codes": ["64483"],
    "payer":           "UnitedHealthcare",   # model must expand "UHC"
    "urgency":         "routine",
}

GROUND_TRUTH["case_007_PT_10202_messy"] = {
    "patient_id":      "PT-10202",
    "patient_age":     45,
    "diagnosis_codes": ["K21.0"],
    "procedure_codes": ["43239"],
    "payer":           "UNKNOWN",            # payer was blank in the note
    "urgency":         "urgent",
}
