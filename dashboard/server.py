"""
dashboard/server.py
Lightweight HTTP server that serves the ClearAuth dashboard.
Reads audit.db and appeal letters to power the UI.

Usage: python dashboard/server.py
Then open: http://localhost:8000
"""
import sys
import json
import sqlite3
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

BASE_DIR   = Path(__file__).parent.parent
DB_PATH    = BASE_DIR / "outputs" / "audit.db"
APPEAL_DIR = BASE_DIR / "outputs" / "appeal_letters"
DASH_DIR   = Path(__file__).parent


def get_stats() -> dict:
    """Read audit.db and compute dashboard metrics."""
    if not DB_PATH.exists():
        return {"total": 0, "approved": 0, "denied": 0, "pending": 0,
                "appeals": 0, "avg_confidence": 0, "cases": [], "payer_breakdown": {}}

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT timestamp, case_id, action, payer, status, confidence FROM audit_log ORDER BY id"
    ).fetchall()
    conn.close()

    decisions = [r for r in rows if r[2] == "pa_decision"]
    appeals   = [r for r in rows if r[2] == "appeal_generated"]
    scores    = [r[5] for r in decisions if r[5] is not None]

    status_counts = {"approved": 0, "denied": 0, "pending_info": 0}
    payer_counts  = {}
    cases         = []

    for r in decisions:
        ts, cid, _, payer, status, conf = r
        status_counts[status] = status_counts.get(status, 0) + 1
        payer_counts[payer]   = payer_counts.get(payer, 0) + 1
        has_appeal = any(a[1] == cid for a in appeals)
        cases.append({
            "case_id":    cid,
            "timestamp":  ts[:19].replace("T", " "),
            "payer":      payer or "Unknown",
            "status":     status,
            "confidence": round((conf or 0) * 100),
            "has_appeal": has_appeal,
        })

    cases.reverse()  # newest first

    return {
        "total":         len(decisions),
        "approved":      status_counts.get("approved", 0),
        "denied":        status_counts.get("denied", 0),
        "pending":       status_counts.get("pending_info", 0),
        "appeals":       len(appeals),
        "avg_confidence": round((sum(scores) / len(scores) * 100) if scores else 0),
        "cases":         cases,
        "payer_breakdown": payer_counts,
    }


def get_appeal(case_id: str) -> str:
    """Return the appeal letter text for a given case ID."""
    for f in APPEAL_DIR.glob(f"{case_id}_appeal.txt"):
        return f.read_text(encoding="utf-8")
    return "No appeal letter found for this case."


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silence default logging

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path, content_type: str):
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/") or "/"

        if path == "/" or path == "/index.html":
            self.send_file(DASH_DIR / "index.html", "text/html")
        elif path == "/api/stats":
            self.send_json(get_stats())
        elif path.startswith("/api/appeal/"):
            case_id = path.split("/")[-1]
            self.send_json({"letter": get_appeal(case_id)})
        else:
            self.send_response(404)
            self.end_headers()


def main():
    port = 8000
    print(f"\n  ClearAuth Dashboard")
    print(f"  Running at: http://localhost:{port}")
    print(f"  Press Ctrl+C to stop\n")
    HTTPServer(("", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
