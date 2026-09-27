#!/usr/bin/env python3
"""
nuDesk Ingestion Pipeline Bridge
Ingests incoming call transcripts and applications from external webhooks
(Read AI, Fireflies.ai, Zoom, Google Drive Intake, Google Forms) directly into
nuDesk FIFO operational queue with active SLA tracking.
"""
import sys
import os
import json
import argparse

# Ensure parent directory is in Python path for database access
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database


def ingest_file(
    module_type: str,
    entity_name: str,
    headline_metric: str,
    transcript_text: str,
    source_channel: str = "Google Meet via Read AI",
    doc_url: str = "",
    doc_note: str = "",
    assessment_summary: str = "Awaiting discovery analysis",
    metadata_extra: dict = None
) -> dict:
    """Ingest a pending record into the nuDesk operational queue."""
    record_id = database.ingest_pending_record(
        module_type=module_type,
        entity_name=entity_name,
        headline_metric=headline_metric,
        transcript_text=transcript_text,
        assessment_summary=assessment_summary,
        source_channel=source_channel,
        doc_url=doc_url,
        doc_note=doc_note,
        metadata_extra=metadata_extra
    )
    return {
        "success": True,
        "record_id": record_id,
        "module_type": module_type,
        "entity_name": entity_name,
        "headline_metric": headline_metric,
        "source_channel": source_channel,
        "status": "Pending Triage",
        "message": f"Successfully queued {entity_name} in {module_type.upper()} operational queue (Record #{record_id})."
    }


def main():
    parser = argparse.ArgumentParser(description="Ingest incoming transcript or document into nuDesk triage queue.")
    parser.add_argument("--module", choices=["credit", "sales", "hr"], help="Target module (credit, sales, hr)")
    parser.add_argument("--entity", help="Entity or applicant name")
    parser.add_argument("--metric", help="Headline metric (e.g. '$150,000 USD | Working Capital')")
    parser.add_argument("--transcript", help="Raw transcript text")
    parser.add_argument("--transcript-file", help="Path to transcript text or json file")
    parser.add_argument("--source", default="Google Meet via Read AI", help="Source channel")
    parser.add_argument("--doc-url", default="", help="Supporting document or quote URL")
    parser.add_argument("--doc-note", default="", help="Note on supporting document")
    parser.add_argument("--summary", default="Awaiting discovery analysis", help="Initial summary")
    parser.add_argument("--stdin", action="store_true", help="Read JSON payload from standard input")

    args = parser.parse_args()

    if args.stdin or not (args.module and args.entity):
        # Try reading JSON from stdin
        if not sys.stdin.isatty():
            try:
                payload = json.load(sys.stdin)
                res = ingest_file(
                    module_type=payload.get("module_type", "credit"),
                    entity_name=payload.get("entity_name", "Unknown Entity"),
                    headline_metric=payload.get("headline_metric", "Pending Assessment"),
                    transcript_text=payload.get("transcript", payload.get("transcript_text", "")),
                    source_channel=payload.get("source_channel", "External Webhook"),
                    doc_url=payload.get("doc_url", ""),
                    doc_note=payload.get("doc_note", ""),
                    assessment_summary=payload.get("summary", "Awaiting discovery analysis"),
                    metadata_extra=payload.get("metadata", {})
                )
                print(json.dumps(res, indent=2))
                return
            except Exception as e:
                print(json.dumps({"success": False, "error": f"Failed to parse stdin JSON: {str(e)}"}))
                sys.exit(1)
        else:
            parser.print_help()
            sys.exit(1)

    transcript = args.transcript or ""
    if args.transcript_file and os.path.exists(args.transcript_file):
        with open(args.transcript_file, "r", encoding="utf-8") as f:
            transcript = f.read()

    res = ingest_file(
        module_type=args.module,
        entity_name=args.entity,
        headline_metric=args.metric or "Pending Metric Assessment",
        transcript_text=transcript,
        source_channel=args.source,
        doc_url=args.doc_url,
        doc_note=args.doc_note,
        assessment_summary=args.summary
    )
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
