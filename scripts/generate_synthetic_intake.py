#!/usr/bin/env python3
"""
Synthetic Meeting Bot & Webhook Generator for nuDesk
Generates realistic, production-schema payloads matching Read AI, Fireflies.ai,
and Google Drive intake webhooks without requiring paid accounts or live bots.
"""
import sys
import os
import json
import argparse
import random
import time
import requests

# Ensure parent directory is in Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "fixtures")


def load_fixture(filename: str) -> dict:
    filepath = os.path.join(FIXTURES_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def generate_synthetic_payload(provider: str = "readai", module: str = "credit") -> dict:
    """Generate or retrieve a realistic synthetic payload matching provider schema."""
    provider = provider.lower()
    module = module.lower()

    if provider == "readai":
        if module == "hr":
            return load_fixture("read_ai_hr_screening.json")
        return load_fixture("read_ai_credit_discovery.json")
    elif provider == "fireflies":
        return load_fixture("fireflies_sales_call.json")
    elif provider == "gdrive":
        return load_fixture("gdrive_intake_quote.json")
    else:
        # Generic synthetic generation
        entity = f"Sierra Freightways {random.randint(10, 99)} LLC (Nogales, AZ)"
        amount = f"${random.randint(90, 350)},000 USD | Working Capital Line"
        return {
            "event": "meeting.completed",
            "meeting_id": f"sim_meet_{random.randint(100000, 999999)}",
            "title": f"Discovery Call - {entity}",
            "bot_source": "Google Meet via Read AI",
            "headline_metric": amount,
            "client_name": entity,
            "department": module,
            "full_transcript_text": f"[00:00:01] Underwriter: Meeting with {entity} regarding commercial line expansion...",
            "summary": f"Discovery call completed with {entity}. Awaiting underwriting analysis."
        }


def extract_ingestion_fields(raw_payload: dict, provider: str, module: str) -> dict:
    """Extract standard fields for nuDesk queue from vendor-specific payload."""
    if provider == "fireflies":
        data = raw_payload.get("data", {})
        entity = data.get("client_name") or data.get("title", "Incoming Fireflies Call")
        metric = data.get("headline_metric", "Commercial Pipeline Lead")
        transcript = data.get("full_transcript_text", "")
        source = data.get("bot_source", "Google Meet via Fireflies.ai")
        summary = data.get("summary", {}).get("overview", "Fireflies.ai transcription completed.")
        doc_url = data.get("transcript_url", "")
        doc_note = f"Fireflies Recording (Duration: {data.get('duration', 0)}s)"
        mod = data.get("department", module)
    elif provider == "gdrive":
        entity = raw_payload.get("client_name") or raw_payload.get("name", "Drive Document Intake")
        metric = raw_payload.get("extracted_metric", "Document Intake")
        transcript = raw_payload.get("text_content", "")
        source = "Google Drive Intake"
        summary = f"Uploaded file: {raw_payload.get('name')}"
        doc_url = raw_payload.get("webViewLink", "")
        doc_note = f"Drive File: {raw_payload.get('name')} ({raw_payload.get('size')} bytes)"
        mod = raw_payload.get("department", module)
    else:
        # Read AI schema
        entity = raw_payload.get("client_name") or raw_payload.get("title", "Read AI Meeting")
        metric = raw_payload.get("headline_metric", "Discovery Call")
        transcript = raw_payload.get("full_transcript_text", "")
        source = raw_payload.get("bot_source", "Google Meet via Read AI")
        summary = raw_payload.get("summary", "Read AI discovery completed.")
        doc_url = raw_payload.get("recording_url", "")
        doc_note = f"Read AI Meeting (Duration: {raw_payload.get('duration_minutes', 30)} min)"
        mod = raw_payload.get("department", module)

    return {
        "module_type": mod.lower(),
        "entity_name": entity,
        "headline_metric": metric,
        "transcript_text": transcript,
        "source_channel": source,
        "assessment_summary": summary,
        "doc_url": doc_url,
        "doc_note": doc_note,
        "metadata_extra": raw_payload
    }


def main():
    parser = argparse.ArgumentParser(description="Simulate synthetic incoming meeting bot & webhook streams.")
    parser.add_argument("--provider", choices=["readai", "fireflies", "gdrive"], default="readai", help="Bot provider schema")
    parser.add_argument("--module", choices=["credit", "sales", "hr"], default="credit", help="Target module")
    parser.add_argument("--dispatch-n8n", action="store_true", help="Post webhook payload directly to local n8n container")
    parser.add_argument("--webhook-url", default="http://localhost:5678/webhook/incoming-meeting", help="n8n webhook URL")
    parser.add_argument("--json-out", action="store_true", help="Print raw vendor JSON schema only")

    args = parser.parse_args()

    payload = generate_synthetic_payload(provider=args.provider, module=args.module)

    if args.json_out:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    # Extract fields and inject into SQLite queue
    norm = extract_ingestion_fields(payload, provider=args.provider, module=args.module)
    rec_id = database.ingest_pending_record(
        module_type=norm["module_type"],
        entity_name=norm["entity_name"],
        headline_metric=norm["headline_metric"],
        transcript_text=norm["transcript_text"],
        assessment_summary=norm["assessment_summary"],
        source_channel=norm["source_channel"],
        doc_url=norm["doc_url"],
        doc_note=norm["doc_note"],
        metadata_extra=norm["metadata_extra"]
    )

    print("=" * 65)
    print(f"Synthetic Ingestion Simulation: {args.provider.upper()} -> nuDesk Queue")
    print("=" * 65)
    print(f"Entity:         {norm['entity_name']}")
    print(f"Module:         {norm['module_type'].upper()}")
    print(f"Headline:       {norm['headline_metric']}")
    print(f"Source Channel: {norm['source_channel']}")
    print(f"Record ID:      #{rec_id} (Active SLA Clock Started)")
    print(f"Triage Status:  Pending (Visible in nuDesk Queue Panel)")

    if args.dispatch_n8n:
        try:
            res = requests.post(args.webhook_url, json=payload, timeout=3)
            print(f"n8n Webhook:    POST {args.webhook_url} -> HTTP {res.status_code}")
        except Exception as e:
            print(f"n8n Webhook:    Could not reach {args.webhook_url} ({str(e)})")

    print("=" * 65)


if __name__ == "__main__":
    main()
