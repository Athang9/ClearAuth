"""
generate_synthetic.py
Generates synthetic clinical note PDFs and PA case JSON files.
Designed to produce a realistic mix: ~5 denials, 2-3 approvals, 1-2 pending.
Run this FIRST before anything else.
Usage: python data/generate_synthetic.py
"""
import json
import random
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

OUTPUT_DIR = Path(__file__).parent
PDF_DIR    = OUTPUT_DIR / "synthetic_pdfs"
CASES_DIR  = OUTPUT_DIR / "synthetic_cases"
PDF_DIR.mkdir(exist_ok=True)
CASES_DIR.mkdir(exist_ok=True)

CASES = [
    # ── APPROVED cases ────────────────────────────────────────────────────────
    {
        "patient_id": "PT-10042",
        "patient_age": 67,
        "patient_name": "James R. Mitchell",
        "diagnosis_codes": ["M16.11", "M25.361"],
        "procedure_codes": ["27447"],
        "procedure_name": "Total Knee Arthroplasty",
        "justification": (
            "Patient presents with severe end-stage osteoarthritis of the right knee (M16.11), "
            "with complete loss of joint space on weight-bearing X-ray. Conservative management "
            "including 18 months of physical therapy, NSAIDs, and two corticosteroid injections "
            "has failed to provide adequate relief. Patient's functional status is significantly "
            "impaired — unable to ambulate more than 50 feet without pain. Total knee replacement "
            "is medically necessary to restore mobility and quality of life."
        ),
        "payer": "UnitedHealthcare",
        "provider": "Dr. Sarah Okonkwo, MD — Orthopedic Surgery",
        "urgency": "routine",
        "expected": "approved"
    },
    {
        "patient_id": "PT-10073",
        "patient_age": 54,
        "patient_name": "Maria L. Fernandez",
        "diagnosis_codes": ["I25.10", "Z82.49"],
        "procedure_codes": ["93306"],
        "procedure_name": "Echocardiography with Doppler",
        "justification": (
            "Patient presents with new-onset exertional dyspnea and atypical chest pain. "
            "ECG shows non-specific ST changes. Strong family history of coronary artery disease. "
            "Echocardiography is indicated to assess ventricular function and valvular pathology "
            "prior to stress testing. Evaluation is urgent given symptom progression over the "
            "past two weeks. Patient has failed initial medical management."
        ),
        "payer": "Aetna",
        "provider": "Dr. Kevin Park, MD — Cardiology",
        "urgency": "urgent",
        "expected": "approved"
    },
    {
        "patient_id": "PT-10108",
        "patient_age": 38,
        "patient_name": "Ashley N. Brooks",
        "diagnosis_codes": ["M75.1", "M75.121"],
        "procedure_codes": ["29827"],
        "procedure_name": "Arthroscopic Rotator Cuff Repair",
        "justification": (
            "Patient sustained a full-thickness rotator cuff tear confirmed by MRI (M75.121). "
            "Six months of supervised physical therapy and subacromial corticosteroid injections "
            "have failed to restore shoulder function. Patient is a 38-year-old with an active "
            "occupation requiring overhead use of the arm. Surgical repair is medically necessary "
            "to prevent further tendon retraction and permanent loss of shoulder function."
        ),
        "payer": "UnitedHealthcare",
        "provider": "Dr. Marcus Webb, MD — Orthopedic Surgery",
        "urgency": "urgent",
        "expected": "approved"
    },

    # ── PENDING cases ─────────────────────────────────────────────────────────
    {
        "patient_id": "PT-10091",
        "patient_age": 44,
        "patient_name": "David A. Thompson",
        "diagnosis_codes": ["K21.0", "K22.70"],
        "procedure_codes": ["43239"],
        "procedure_name": "Upper GI Endoscopy with Biopsy",
        "justification": (
            "Patient has a 5-year history of GERD with recent worsening of symptoms. "
            "New onset dysphagia and 12-pound unintentional weight loss over 3 months. "
            "Upper endoscopy with biopsy is necessary to rule out Barrett's esophagus."
        ),
        "payer": "Cigna",
        "provider": "Dr. Rachel Kim, MD — Gastroenterology",
        "urgency": "routine",
        "expected": "pending"
    },

    # ── DENIED cases ──────────────────────────────────────────────────────────
    {
        "patient_id": "PT-10127",
        "patient_age": 71,
        "patient_name": "Robert H. Nguyen",
        "diagnosis_codes": ["G89.29", "M47.816"],
        "procedure_codes": ["64483"],
        "procedure_name": "Transforaminal Epidural Steroid Injection",
        "justification": (
            "Chronic lumbar radiculopathy secondary to L4-L5 foraminal stenosis. "
            "Three months of PT and oral analgesics have provided inadequate relief."
        ),
        "payer": "Aetna",
        "provider": "Dr. Linda Chen, MD — Pain Management",
        "urgency": "routine",
        "expected": "denied"
    },
    {
        "patient_id": "PT-10155",
        "patient_age": 62,
        "patient_name": "Patricia M. Jones",
        "diagnosis_codes": ["M54.4", "M51.16"],
        "procedure_codes": ["22551"],
        "procedure_name": "Anterior Cervical Discectomy and Fusion",
        "justification": (
            "Cervical disc herniation at C5-C6. Patient reports neck pain. "
            "Has tried PT for 4 weeks."
        ),
        "payer": "BlueCross BlueShield",
        "provider": "Dr. James Rivera, MD — Neurosurgery",
        "urgency": "routine",
        "expected": "denied"
    },
    {
        "patient_id": "PT-10178",
        "patient_age": 29,
        "patient_name": "Kevin O. Williams",
        "diagnosis_codes": ["F32.1", "Z96.89"],
        "procedure_codes": ["90837"],
        "procedure_name": "Psychotherapy 60 minutes",
        "justification": (
            "Patient with depression. Requesting psychotherapy sessions."
        ),
        "payer": "Humana",
        "provider": "Dr. Aisha Patel, PhD — Psychology",
        "urgency": "routine",
        "expected": "denied"
    },
    {
        "patient_id": "PT-10199",
        "patient_age": 55,
        "patient_name": "Sandra K. Oyelaran",
        "diagnosis_codes": ["M54.5", "M51.36"],
        "procedure_codes": ["27130"],
        "procedure_name": "Total Hip Arthroplasty",
        "justification": (
            "Low back pain. Patient requests hip replacement. "
            "No imaging provided. No prior conservative treatment documented."
        ),
        "payer": "Cigna",
        "provider": "Dr. Thomas Okafor, MD — Orthopedic Surgery",
        "urgency": "routine",
        "expected": "denied"
    },
    {
        "patient_id": "PT-10214",
        "patient_age": 48,
        "patient_name": "Michael B. Torres",
        "diagnosis_codes": ["J45.50", "J30.9"],
        "procedure_codes": ["31622"],
        "procedure_name": "Bronchoscopy",
        "justification": (
            "Asthma and allergic rhinitis. Patient wants bronchoscopy."
        ),
        "payer": "Aetna",
        "provider": "Dr. Elena Vasquez, MD — Pulmonology",
        "urgency": "routine",
        "expected": "denied"
    },
]


def generate_pdf(case: dict, output_path: Path):
    doc    = SimpleDocTemplate(str(output_path), pagesize=letter,
                               topMargin=inch, bottomMargin=inch,
                               leftMargin=inch, rightMargin=inch)
    styles = getSampleStyleSheet()
    story  = []

    def p(text, style="Normal", space_after=0.1):
        story.append(Paragraph(text, styles[style]))
        story.append(Spacer(1, space_after * inch))

    p("<b>PRIOR AUTHORIZATION REQUEST — CLINICAL NOTE</b>", "Heading1", 0.15)
    p(f"<b>Date:</b> March 28, 2026")
    p(f"<b>Patient ID:</b> {case['patient_id']}")
    p(f"<b>Patient Name:</b> {case['patient_name']}")
    p(f"<b>Date of Birth:</b> Age {case['patient_age']}")
    p(f"<b>Ordering Provider:</b> {case['provider']}")
    p(f"<b>Insurance / Payer:</b> {case['payer']}")
    p(f"<b>Member ID:</b> MBR-{random.randint(100000, 999999)}")
    story.append(Spacer(1, 0.1 * inch))

    p("<b>REQUESTED PROCEDURE</b>", "Heading2", 0.1)
    p(f"<b>Procedure Name:</b> {case['procedure_name']}")
    p(f"<b>CPT Code(s):</b> {', '.join(case['procedure_codes'])}")
    p(f"<b>ICD-10 Diagnosis Code(s):</b> {', '.join(case['diagnosis_codes'])}")
    p(f"<b>Urgency:</b> {case['urgency'].capitalize()}")
    story.append(Spacer(1, 0.1 * inch))

    p("<b>CLINICAL JUSTIFICATION</b>", "Heading2", 0.1)
    p(case["justification"], space_after=0.15)

    p("<b>ATTESTATION</b>", "Heading2", 0.1)
    p("I attest that the above information is accurate and that the requested procedure "
      "is medically necessary for this patient based on current clinical guidelines.",
      space_after=0.2)
    p(f"<b>Signature:</b> {case['provider']}")
    p("<b>Date:</b> March 28, 2026")
    p("<br/><i>DISCLAIMER: Synthetic document for software demonstration. "
      "All patient information is fictional. No real PHI.</i>")

    doc.build(story)
    print(f"  Created: {output_path.name}  [{case.get('expected','?').upper()}]")


def generate_case_json(case: dict, output_path: Path):
    with open(output_path, "w") as f:
        json.dump(case, f, indent=2)


def main():
    print("Generating synthetic clinical note PDFs...")
    for i, case in enumerate(CASES, 1):
        fname = f"case_{i:03d}_{case['patient_id'].replace('-','_')}"
        generate_pdf(case, PDF_DIR / f"{fname}.pdf")
        generate_case_json(case, CASES_DIR / f"{fname}.json")

    approved = sum(1 for c in CASES if c.get('expected') == 'approved')
    denied   = sum(1 for c in CASES if c.get('expected') == 'denied')
    pending  = sum(1 for c in CASES if c.get('expected') == 'pending')

    print(f"\nDone! Generated {len(CASES)} PDFs:")
    print(f"  Expected: {approved} approved, {denied} denied, {pending} pending")
    print(f"\nRun all cases:")
    for i, case in enumerate(CASES, 1):
        fname = f"case_{i:03d}_{case['patient_id'].replace('-','_')}"
        print(f"  python src/pipeline.py data/synthetic_pdfs/{fname}.pdf")


if __name__ == "__main__":
    main()
