# ClearAuth — System Architecture

## Overview

ClearAuth is a Python-based AI pipeline that automates the prior
authorization (PA) workflow from document intake through decision
and appeal generation.

---

## Pipeline Flow

```
Clinical Note PDF
       |
       v
[1] document_intake.py
    - Extract text from PDF
    - Send to Claude API
    - Return structured fields (ICD-10, CPT, justification, payer)
       |
       v
[2] pa_engine.py
    - Load payer policy (JSON)
    - Score request against criteria
    - Return PADecision (status + confidence + reason)
       |
       v
  [Decision Gate]
  /            \
APPROVED      DENIED
  |              |
  v              v
Audit log   [3] appeals_generator.py
                 - Send denial + clinical context to Claude
                 - Generate formal appeal letter
                 - Save to outputs/appeal_letters/
                 |
                 v
            Audit log
```

---

## Component Map

| File | Role |
|------|------|
| `src/models.py` | Pydantic data models — single source of truth for all data shapes |
| `src/document_intake.py` | PDF text extraction + Claude API field extraction |
| `src/pa_engine.py` | Payer policy matching + confidence scoring |
| `src/appeals_generator.py` | AI-generated appeal letter drafting |
| `src/audit_logger.py` | SQLite audit trail — every action logged |
| `src/metrics.py` | Aggregate metrics from audit log → Markdown report |
| `src/pipeline.py` | Orchestrator — wires all components together |
| `data/generate_synthetic.py` | Generates test PDFs and case JSON files |
| `data/payer_policies/*.json` | Payer criteria knowledge base |

---

## Data Flow (No PHI Persisted)

```
PDF Input
  → Text extracted in memory
  → Structured fields extracted by Claude
  → Fields used for decision scoring
  → Only case_id + metadata written to audit.db
  → Free-text clinical note NOT stored
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| AI | Google Gemini API (gemini-1.5-pro) |
| Data validation | Pydantic v2 |
| PDF extraction | pypdf |
| PDF generation | reportlab |
| Audit storage | SQLite |
| Config | python-dotenv |
| Testing | pytest |

---

## Production Architecture (What This Would Become)

```
                    ┌─────────────────┐
                    │   EHR System    │  (Epic, Cerner)
                    └────────┬────────┘
                             │ HL7 FHIR / PDF
                             v
                    ┌─────────────────┐
                    │  API Gateway    │  (Rate limiting, Auth)
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              v              v              v
       ┌──────────┐  ┌──────────────┐  ┌──────────┐
       │ Intake   │  │  PA Engine   │  │ Appeals  │
       │ Service  │  │  Service     │  │ Service  │
       └──────────┘  └──────────────┘  └──────────┘
              \              |              /
               v             v             v
              ┌─────────────────────────────┐
              │     PostgreSQL (encrypted)  │
              │     + Audit Log             │
              └─────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │   Dashboard     │
                    │ (React frontend)│
                    └─────────────────┘
```

*All cloud services would be HIPAA-eligible. BAAs signed before any PHI processed.*
