#!/usr/bin/env python3
"""
nuDesk Inbound Operations API
Zero-dependency HTTP ingestion listener for n8n, Google Sheets, and webhook intake.
Runs on port 8502 by default, forwarding inbound payloads directly into the
nuDesk FIFO operational queue with active SLA tracking.
"""
import os
import sys
import json
import time
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Tuple, Dict, Any, Optional

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database

DEFAULT_PORT = int(os.getenv("NUDESK_INGEST_PORT", "8502"))
DEFAULT_HOST = os.getenv("NUDESK_INGEST_HOST", "0.0.0.0")
DEFAULT_AUTH_TOKEN = os.getenv("N8N_AUTH_TOKEN", "nudesk_ops_secure_token_v2")

_server_instance: Optional[HTTPServer] = None
_server_thread: Optional[threading.Thread] = None


class IngestionRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for inbound triage ingestion."""

    def _set_headers(self, status_code: int = 200, content_type: str = "application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-nuDesk-Auth-Token, Authorization")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        if self.path == "/api/health" or self.path == "/":
            response = {
                "status": "healthy",
                "service": "nuDesk Inbound Ingestion API",
                "port": self.server.server_port,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "endpoints": [
                    "POST /api/ingest",
                    "POST /api/simulate-google-sheet-intake",
                    "GET /api/health"
                ]
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(response).encode("utf-8"))
        elif self.path == "/api/pending":
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, module_type, entity_name, headline_metric, timestamp, source_channel
                FROM operations_history
                WHERE is_processed = 0
                ORDER BY timestamp DESC LIMIT 20
            """)
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            self._set_headers(200)
            self.wfile.write(json.dumps({"pending_count": len(rows), "records": rows}).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)

        try:
            body = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except Exception as exc:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": f"Invalid JSON payload: {str(exc)}"}).encode("utf-8"))
            return

        if self.path == "/api/ingest":
            self._handle_ingest(body)
        elif self.path == "/api/simulate-google-sheet-intake":
            self._handle_sheet_intake_simulation(body)
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": f"POST endpoint '{self.path}' not found"}).encode("utf-8"))

    def _handle_ingest(self, body: Dict[str, Any]):
        # Optional auth token validation
        req_token = self.headers.get("X-nuDesk-Auth-Token", "")
        if DEFAULT_AUTH_TOKEN and req_token and req_token != DEFAULT_AUTH_TOKEN:
            self._set_headers(401)
            self.wfile.write(json.dumps({"error": "Unauthorized: Invalid X-nuDesk-Auth-Token"}).encode("utf-8"))
            return

        module_type = body.get("module_type", "credit").lower()
        entity_name = body.get("entity_name") or body.get("company_name") or body.get("applicant_name") or "Inbound Intake"
        headline_metric = body.get("headline_metric") or body.get("loan_amount_requested") or "Awaiting Financial Review"
        transcript_text = body.get("transcript_text") or body.get("transcript") or body.get("notes") or "Raw transcript received via external intake pipeline."
        source_channel = body.get("source_channel") or "Google Sheets Inbound Intake via n8n"
        doc_url = body.get("doc_url", "")
        doc_note = body.get("doc_note", "")
        metadata_extra = body.get("metadata", {})

        record_id = database.ingest_pending_record(
            module_type=module_type,
            entity_name=entity_name,
            headline_metric=headline_metric,
            transcript_text=transcript_text,
            assessment_summary="Awaiting discovery analysis",
            source_channel=source_channel,
            doc_url=doc_url,
            doc_note=doc_note,
            metadata_extra=metadata_extra
        )

        response = {
            "success": True,
            "record_id": record_id,
            "module_type": module_type,
            "entity_name": entity_name,
            "headline_metric": headline_metric,
            "source_channel": source_channel,
            "status": "Queued in nuDesk Studio",
            "message": f"Successfully queued {entity_name} in {module_type.upper()} queue with active SLA.",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        }
        self._set_headers(200)
        self.wfile.write(json.dumps(response).encode("utf-8"))

    def _handle_sheet_intake_simulation(self, body: Dict[str, Any]):
        """Simulate an inbound row added to an external Google Sheet intake form."""
        module_type = body.get("module_type", "credit").lower()
        if module_type == "sales":
            entity_name = body.get("entity_name", "Sonora Cold Logistics SA")
            headline_metric = body.get("headline_metric", "$2,800,000 ARR | 14 Reefer Fleet")
            transcript_text = body.get("transcript_text", "[00:00:10] Inbound Lead Form: Sonora Cold Logistics seeking freight factoring line for cross-border produce.")
        elif module_type == "hr":
            entity_name = body.get("entity_name", "Daniela Mendoza")
            headline_metric = body.get("headline_metric", "Senior Commercial Underwriter Applicant")
            transcript_text = body.get("transcript_text", "[00:00:05] Candidate Intake: Bilingual underwriter with 4 years experience in commercial asset-based lending.")
        else:
            entity_name = body.get("entity_name", "Baja Agro-Transportes S.A. de C.V.")
            headline_metric = body.get("headline_metric", "$350,000 USD | Working Capital Line")
            transcript_text = body.get("transcript_text", "[00:00:02] Broker Intake via Google Sheets: Baja Agro-Transportes requesting $350k working capital. 20 trucks collateralized.")

        body.setdefault("module_type", module_type)
        body.setdefault("entity_name", entity_name)
        body.setdefault("headline_metric", headline_metric)
        body.setdefault("transcript_text", transcript_text)
        body.setdefault("source_channel", "Google Sheets Inbound Intake via n8n")
        self._handle_ingest(body)

    def log_message(self, format, *args):
        # Suppress noisy standard HTTP logs in production
        return


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a TCP port is already open and bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """Run synchronous HTTP server loop."""
    global _server_instance
    server_address = (host, port)
    _server_instance = HTTPServer(server_address, IngestionRequestHandler)
    print(f"[nuDesk Inbound API] Listening on http://{host}:{port} for n8n & Google Sheets intake...")
    try:
        _server_instance.serve_forever()
    except Exception as exc:
        print(f"[nuDesk Inbound API] Server halted: {exc}")


def ensure_server_running(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> bool:
    """
    Ensure the ingestion API daemon is running in the background.
    Safe to call repeatedly; starts background thread if not already active.
    """
    global _server_thread
    if is_port_in_use(port, "127.0.0.1"):
        return True

    try:
        _server_thread = threading.Thread(
            target=run_server,
            args=(host, port),
            daemon=True,
            name="nuDesk-Inbound-API-Thread"
        )
        _server_thread.start()
        time.sleep(0.3)
        return is_port_in_use(port, "127.0.0.1")
    except Exception as exc:
        print(f"[nuDesk Inbound API] Could not start daemon: {exc}")
        return False


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    run_server(port=port)
