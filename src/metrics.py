"""
metrics.py
Reads the audit log and generates a metrics report in Markdown.
Usage: python metrics.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import sqlite3
from collections import Counter
from audit_logger import DB_PATH

REPORT_PATH = Path(__file__).parent.parent / "outputs" / "metrics_report.md"


def generate_report():
    if not DB_PATH.exists():
        print("No audit log found. Run the pipeline on some cases first.")
        return

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT case_id, action, payer, status, confidence FROM audit_log"
    ).fetchall()
    conn.close()

    decisions = [r for r in rows if r[1] == "pa_decision"]
    appeals    = [r for r in rows if r[1] == "appeal_generated"]
    intakes    = [r for r in rows if r[1] == "document_intake"]

    if not decisions:
        print("No PA decisions found yet. Run the pipeline first.")
        return

    statuses = Counter(r[3] for r in decisions)
    payers   = Counter(r[2] for r in decisions)
    scores   = [r[4] for r in decisions if r[4] is not None]
    avg_score = sum(scores) / len(scores) if scores else 0
    total = len(decisions)
    approval_rate = statuses.get("approved", 0) / total * 100 if total else 0
    denial_rate   = statuses.get("denied", 0) / total * 100 if total else 0

    report = f"""# ClearAuth — Pipeline Metrics Report

> **Disclaimer:** All data is synthetic. No real PHI was used.

## Summary

| Metric | Value |
|--------|-------|
| Total cases processed | {total} |
| Documents ingested | {len(intakes)} |
| Approval rate | {approval_rate:.1f}% |
| Denial rate | {denial_rate:.1f}% |
| Avg confidence score | {avg_score:.2f} / 1.00 |
| Appeal letters generated | {len(appeals)} |

## Decisions by Status

| Status | Count | Percentage |
|--------|-------|------------|
| Approved | {statuses.get('approved', 0)} | {statuses.get('approved', 0)/total*100:.1f}% |
| Denied | {statuses.get('denied', 0)} | {statuses.get('denied', 0)/total*100:.1f}% |
| Pending info | {statuses.get('pending_info', 0)} | {statuses.get('pending_info', 0)/total*100:.1f}% |

## Cases by Payer

| Payer | Cases |
|-------|-------|
{"".join(f"| {k} | {v} |" + chr(10) for k, v in payers.most_common())}

## What This Demonstrates

- End-to-end AI pipeline: PDF intake → structured extraction → policy matching → decision
- Every action is audit-logged with timestamp and case ID (HIPAA design pattern)
- Denied cases automatically trigger appeal letter generation
- Confidence scoring enables human-in-the-loop review for borderline cases
"""

    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Report written to: {REPORT_PATH}")
    print()
    print(report)


if __name__ == "__main__":
    generate_report()
