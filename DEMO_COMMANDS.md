# ClearAuth — Complete Demo Command Sequence
## Run these in order during your Friday meeting

### Terminal window 1 — run the pipeline

```bash
# Navigate to project
cd Desktop/Data\ Analyst\ Job\ Prep_India/Data\ Analyst\ Projects/clearauth_FINAL/clearauth

# Activate environment
source venv/Scripts/activate    # Git Bash
# OR
venv\Scripts\activate           # Command Prompt

# Generate test data (only needed once)
python data/generate_synthetic.py

# Case 1 — Total Knee Replacement (UnitedHealthcare) → APPROVED
python src/pipeline.py data/synthetic_pdfs/case_001_PT_10042.pdf

# Case 2 — Cardiac Echo (Aetna) → watch the decision
python src/pipeline.py data/synthetic_pdfs/case_002_PT_10073.pdf

# Case 5 — Epidural Injection (Aetna) → DENIED → appeal letter auto-generated
python src/pipeline.py data/synthetic_pdfs/case_005_PT_10127.pdf

# Show the appeal letter (replace XXXXXXXX with actual case ID from output above)
cat outputs/appeal_letters/XXXXXXXX_appeal.txt

# Messy case — abbreviated clinical note (tests robustness)
python src/pipeline.py data/synthetic_pdfs/case_006_PT_10201_messy.pdf

# Generate metrics report
python src/metrics.py

# Run all 18 tests
python -m pytest tests/ -v
```

### Terminal window 2 — dashboard

```bash
python dashboard/server.py
# Then open browser: http://localhost:8000
```

### What to say at each step

**Running case_001:** "This is a 67-year-old patient with end-stage knee osteoarthritis.
Watch it read the PDF, extract the clinical fields, match against UnitedHealthcare's
policy criteria, and return an approval with a confidence score — all in under 5 seconds."

**Running case_005:** "This one gets denied — the procedure criteria don't fully match.
Watch what happens automatically..."
[wait for appeal letter to generate]
"It just drafted a formal medical appeal letter. Let me open it."

**Showing the messy case:** "This one uses doctor shorthand — 'pt c/o', abbreviations,
an abbreviated payer name. The model still extracts the right fields. That's where the
LLM adds real value over a rules-based parser."

**Showing the dashboard:** "Every case that runs through the pipeline appears here live.
The audit log underneath is designed around HIPAA's technical safeguard requirements —
every action logged with timestamp and case ID, no PHI stored."

**Showing the tests:** "18 automated tests covering the data models, the decision engine,
and the audit logger. The test suite catches regressions before they hit production."
