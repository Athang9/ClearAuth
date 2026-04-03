# ClearAuth — Friday Demo Script
## Meeting with Trellis Co-Founder

---

## Before the Meeting (30 min before)

1. Open your terminal (Command Prompt or PowerShell)
2. Navigate to your project: `cd clearauth`
3. Activate venv: `venv\Scripts\activate`
4. Run the pipeline once to make sure it works: `python src/pipeline.py data/synthetic_pdfs/case_001_PT_10042.pdf`
5. Have your GitHub repo open in the browser
6. Have the slides open and ready on slide 1

---

## The Opening (30 seconds — say this exactly)

> "Before we get started — I spent the last few days building something
> I wanted to show you. It's a working prior authorization pipeline
> that automates document intake, PA decisions, and appeal drafting
> using Claude's API. I built it specifically to understand the problem
> space Trellis is working in. Can I walk you through it quickly?"

---

## Slide Walkthrough (~5 minutes)

### Slide 1 — Title
Just introduce yourself briefly. "This is ClearAuth — a prior auth automation pipeline."

### Slide 2 — The Problem
> "Prior authorizations take an average of 11 days. 93% of physicians
> say PAs delay necessary care. 82% say they sometimes abandon treatment
> because of PA burden. Patients die waiting. That's the problem Trellis
> is solving — and the one I wanted to deeply understand."

### Slide 3 — What Trellis Does
Show you understand their product. Don't read the slide — say it in your own words:
> "Trellis automates this entire workflow — intake, PA submission,
> appeals — at scale. The goal is to turn an 11-day process into
> something that happens in minutes."

### Slide 4 — What I Built
> "So I built a simplified version of this pipeline. Three stages:
> document intake using AI to extract structured fields, a decision
> engine that matches against payer criteria, and an appeals generator
> that auto-drafts letters when cases are denied."

### Slide 5 — Architecture
Walk through the diagram briefly. "PDF goes in, Claude extracts the fields,
we match against payer policy, return a decision with a confidence score,
and if denied, Claude drafts the appeal letter automatically."

### Slide 6 — Live Demo
> "Let me show you the actual code running."

---

## Live Demo (~3 minutes)

Open your terminal. Type slowly and clearly — narrate as you go.

**Step 1 — Show the synthetic PDF**
```
Open: data/synthetic_pdfs/case_001_PT_10042.pdf
```
Say: "This is a synthetic clinical note — totally fake patient data,
generated programmatically. In a real system this would come from an EHR."

**Step 2 — Run the pipeline**
```
python src/pipeline.py data/synthetic_pdfs/case_001_PT_10042.pdf
```
As it runs, narrate each step:
- "Step 1 — it's reading the PDF and sending it to Claude to extract the fields"
- "Step 2 — matching the extracted fields against UnitedHealthcare's policy criteria"
- "Step 3 — it came back approved with 80% confidence — no appeal needed"

**Step 3 — Run a denial case**
```
python src/pipeline.py data/synthetic_pdfs/case_005_PT_10127.pdf
```
Say: "Let me show you a denial. This patient's procedure didn't match
the payer criteria..."
When it generates the appeal: "And now it automatically drafts the appeal letter.
Let me open that."
```
Open: outputs/appeal_letters/<case_id>_appeal.txt
```

**Step 4 — Show the audit log**
```
python src/metrics.py
```
Say: "Every single action is logged — timestamps, case IDs, outcomes.
This is the foundation of a HIPAA-compliant audit trail."

---

## Slide 7 — HIPAA Slide
> "I also wrote a full compliance design document. I know Trellis
> operates in a world where HIPAA is non-negotiable, so I wanted to
> think through what it would take to make this production-ready —
> encryption at rest, audit controls, BAAs with Anthropic, data
> minimization. It's all in the COMPLIANCE.md in the repo."

---

## Slide 8 — What I'd Build Next
> "If I were joining the team, here's what I'd tackle next:
> a React dashboard for the ops team, expanding the payer policy
> knowledge base, and FHIR integration to connect directly with EHRs.
> But more importantly — I'd want to talk to your customers to
> understand what's actually slowing them down."

---

## The Close (say this)
> "I built this in 3 days because I wanted to show up having already
> thought deeply about your problem space. I know Trellis is moving
> fast, and I want to be someone who adds value from day one.
> What are the biggest operational bottlenecks you're seeing right now?"

Then STOP TALKING. Let them respond. Listen more than you speak.

---

## Questions They Might Ask — Your Answers

**"How does the PA engine actually decide approval?"**
> "It loads a payer policy JSON — which contains the approved procedure codes
> and required diagnosis codes — then scores the request across four criteria:
> procedure coverage, diagnosis alignment, urgency, and documentation quality.
> Each criterion contributes to a confidence score between 0 and 1."

**"Is this HIPAA compliant?"**
> "As a demo — no, because it uses SQLite and has no auth. But it's designed
> around HIPAA principles: audit logging, data minimization, no PHI persisted.
> I wrote a full COMPLIANCE.md that documents what production would need —
> AES-256 at rest, TLS 1.3, a BAA with Anthropic's enterprise tier, VPC
> networking. I wanted to show I'd thought about it seriously."

**"Why did you use Claude instead of GPT?"**
> "Trellis uses Claude — and honestly, Claude's instruction-following for
> structured JSON extraction is excellent. The prompts I wrote are very
> specific about schema, and Claude returns clean JSON reliably."

**"What would you do differently?"**
> "In production I'd replace the JSON policy files with a vector database
> so we can do semantic matching against payer criteria documents. I'd also
> add a human-in-the-loop review step for borderline confidence scores —
> anything between 0.5 and 0.75 should go to a human reviewer before
> sending to the payer."

**"Have you worked in healthcare before?"**
> "Not professionally, but I spent time researching the PA workflow
> specifically for this project — I read CMS guidelines, looked at public
> payer policy documents from UHC and Aetna, and studied how ICD-10 and
> CPT codes map to coverage decisions. I wanted to build something that
> reflects how the system actually works."

---

## After the Meeting

Send a follow-up email within 2 hours:
- Thank them for their time
- Attach the GitHub link again
- Mention one specific thing they said that resonated with you
- Restate your enthusiasm for the role

---

*Good luck. You've got this.*
