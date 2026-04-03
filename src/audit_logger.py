"""
audit_logger.py
HIPAA-aware audit trail. Logs every pipeline action to SQLite
with timestamp, case ID, action type, and outcome.
No PHI is stored in the log — only case IDs and metadata.
"""
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "outputs" / "audit.db"


def init_db():
    """Create the audit table if it doesn't exist yet."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp     TEXT    NOT NULL,
            case_id       TEXT    NOT NULL,
            action        TEXT    NOT NULL,
            payer         TEXT,
            status        TEXT,
            confidence    REAL,
            details       TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_event(
    case_id: str,
    action: str,
    payer: str = None,
    status: str = None,
    confidence: float = None,
    details: dict = None
):
    """
    Log a pipeline event.
    Actions: document_intake | pa_decision | appeal_generated
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT INTO audit_log
           (timestamp, case_id, action, payer, status, confidence, details)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.now(timezone.utc).isoformat(),
            case_id,
            action,
            payer,
            status,
            confidence,
            json.dumps(details or {})
        )
    )
    conn.commit()
    conn.close()


def get_all_events() -> list[dict]:
    """Return all audit log entries as a list of dicts."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT timestamp, case_id, action, payer, status, confidence FROM audit_log ORDER BY id"
    ).fetchall()
    conn.close()
    return [
        {"timestamp": r[0], "case_id": r[1], "action": r[2],
         "payer": r[3], "status": r[4], "confidence": r[5]}
        for r in rows
    ]
