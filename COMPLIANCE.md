# HIPAA Compliance Design Document

## Synthetic Data Disclaimer

> **No real Protected Health Information (PHI) was used in this project.**
> All patient names, IDs, diagnoses, and clinical notes are generated
> programmatically using synthetic data tools. This project is a portfolio
> demonstration only.

---

## Why HIPAA Matters Here

Prior authorization workflows handle some of the most sensitive patient data
in healthcare: diagnoses, procedures, clinical notes, and payer decisions.
Any production system in this space must be designed with HIPAA compliance
as a first-class concern — not an afterthought.

This document describes how ClearAuth would be architected for HIPAA
compliance in a production environment.

---

## Technical Safeguards (45 CFR § 164.312)

### Encryption
| Layer | Standard |
|-------|----------|
| Data at rest | AES-256 (AWS S3 + RDS encryption) |
| Data in transit | TLS 1.3 for all API calls |
| API keys | Stored in environment variables, never in code |

### Access Controls
- Role-based access control (RBAC): `clinician | admin | viewer`
- Multi-factor authentication (MFA) required for all roles
- Principle of least privilege — each role sees only what it needs
- Session tokens expire after 15 minutes of inactivity

### Audit Controls (implemented in `audit_logger.py`)
Every pipeline action is logged with:
- UTC timestamp
- Case ID (not patient name — no PHI in logs)
- Action type: `document_intake | pa_decision | appeal_generated`
- Payer name
- Decision status and confidence score

Audit logs are append-only and retained for a minimum of 6 years per HIPAA requirements.

### Data Minimization
- Only fields required for PA processing are extracted from clinical notes
- Free-text clinical notes are processed in-memory and NOT persisted
- Patient names are not stored in the pipeline database
- PHI is purged after configurable retention period (default: 7 years)

---

## Administrative Safeguards (45 CFR § 164.308)

### Business Associate Agreements (BAAs)
Production deployment requires BAAs with:
- **Cloud provider**: AWS, GCP, and Azure all offer HIPAA-eligible services and BAAs
- **Anthropic**: Enterprise tier includes BAA for Claude API usage
- **Any third-party OCR service**: Must sign BAA before processing PHI

### Workforce
- HIPAA training required for all staff with system access
- Designated Privacy Officer and Security Officer
- Annual risk assessments

---

## Physical Safeguards (45 CFR § 164.310)

- All compute in HIPAA-eligible cloud regions
- No PHI ever on developer laptops or local machines
- Production database accessible only via VPN + MFA

---

## Incident Response

Per HIPAA Breach Notification Rule (45 CFR § 164.400):
- Affected individuals notified within 60 days of discovery
- HHS notified within 60 days
- Media notification if breach affects 500+ individuals in a state

Automated alerting is configured for:
- Anomalous query volumes (potential data exfiltration)
- Failed authentication attempts
- Access outside business hours from unrecognized IPs

---

## What Is NOT Implemented in This Demo

This is a portfolio project. The following production requirements are
NOT implemented and must be added before any real PHI is processed:

| Feature | Demo Status | Production Requirement |
|---------|-------------|----------------------|
| Database encryption | Not implemented | AES-256 at rest |
| User authentication | Not implemented | OAuth 2.0 + MFA |
| Network security | Not implemented | VPC + WAF |
| BAAs signed | Not applicable | Required before launch |
| Pen testing | Not done | Required annually |
| PHI in logs | No PHI logged | Verified by log scanner |

---

*ClearAuth — Built with HIPAA design principles. Synthetic data only.*
