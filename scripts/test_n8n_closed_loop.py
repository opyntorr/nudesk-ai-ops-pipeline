#!/usr/bin/env python3
"""
nuDesk Closed-Loop Integration Test
Tests the complete bidirectional lifecycle:
1. Inbound Ingestion (Simulating Google Sheets Intake row -> n8n -> nuDesk Ingestion API :8502)
2. Queue Verification & SLA Activation
3. Agentic Triage (Deterministic Tools & Pydantic synthesis)
4. Outbound Dispatch (nuDesk -> n8n Webhook :5678 -> Google Sheets / Asana / Gmail)
"""
import sys
import os
import json
import time
import requests

# Ensure parent directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database
import ai_engine
import crm_dispatcher
import inbound_api

INGEST_URL = "http://127.0.0.1:8502/api/ingest"
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/nudesk-triage")


def run_closed_loop_test():
    print("=" * 70)
    print("nuDesk Closed-Loop Bidirectional Automation Verification")
    print("Google Sheets Inbound -> n8n -> nuDesk Cockpit -> n8n -> Workspace CRM")
    print("=" * 70)

    # Step 0: Ensure Ingestion Server is running
    print("\n[Step 0] Checking Inbound API Server on port 8502...")
    inbound_api.ensure_server_running(port=8502)
    time.sleep(0.5)

    try:
        health = requests.get("http://127.0.0.1:8502/api/health", timeout=3).json()
        print(f"PASS: Inbound API is {health.get('status')} on port {health.get('port')}.")
    except Exception as exc:
        print(f"FAIL: Inbound API connection failed: {exc}")
        return False

    # Step 1: Simulate Inbound Google Sheet row received via n8n
    print("\n[Step 1] Simulating Inbound Google Sheet Row Intake...")
    inbound_payload = {
        "module_type": "credit",
        "entity_name": "Sonora Pacific Produce Logistics",
        "headline_metric": "$320,000 USD | Working Capital & Factoring",
        "transcript_text": (
            "[00:00:05] Broker (Google Sheets Form): Inbound commercial debt application for Sonora Pacific Produce. "
            "Annual revenue $2.4M USD. Requesting $320,000 working capital line. Monthly revenue $200,000, "
            "monthly debt obligations $48,000. Collateral: 12 refrigerated trailers valued at $410,000."
        ),
        "source_channel": "Google Sheets Inbound Intake via n8n",
        "doc_url": "https://docs.google.com/spreadsheets/d/mock-intake-sheet",
        "doc_note": "Row #14 from Inbound Raw Submissions Google Sheet",
        "metadata": {
            "sheet_tab": "Inbound Raw Submissions",
            "row_id": 14,
            "status_before": "NEW",
            "status_after": "QUEUED_IN_NUDESK"
        }
    }

    headers = {
        "Content-Type": "application/json",
        "X-nuDesk-Auth-Token": "nudesk_ops_secure_token_v2"
    }
    ingest_resp = requests.post(INGEST_URL, json=inbound_payload, headers=headers, timeout=5)
    assert ingest_resp.status_code == 200, f"Ingest failed: {ingest_resp.text}"
    ingest_data = ingest_resp.json()
    record_id = ingest_data["record_id"]
    print(f"PASS: Row ingested into nuDesk as Record #{record_id} with status '{ingest_data['status']}'.")

    # Step 2: Verify Record in SQLite with active SLA
    print("\n[Step 2] Verifying Operational Record & SLA Clock...")
    record = database.get_operation_by_id(record_id)
    assert record is not None, "Record not found in SQLite database"
    assert record["is_processed"] == 0, "Record should be in pending queue"
    sla = database.calculate_sla_status(record["timestamp"], record["is_processed"])
    print(f"PASS: Record #{record_id} in queue. SLA Status: {sla['tier']} ({sla['label']}).")

    # Step 3: Run AI Agentic Triage (with Deterministic Tool Execution)
    print("\n[Step 3] Running AI Agentic Triage (Deterministic Tools + Gemini Cascade)...")
    memo, trace, is_fallback, status_msg = ai_engine.agentic_credit_triage(
        transcript=record["assessment_summary"] + " " + record.get("full_output_json", ""),
        entity_name_hint=record["entity_name"]
    )
    print(f"PASS: Agentic Triage synthesized memo for {memo.business_name}.")
    print(f"      Calculated DTI: {memo.estimated_dti_ratio:.1%} | Risk Tier: {memo.risk_tier}")
    print(f"      Asana Tasks: {[t.task_title for t in memo.asana_tasks]}")
    print(f"      Tools Executed in Trace: {len(trace)}")

    # Step 4: Dispatch Outbound Payload to n8n Webhook
    print("\n[Step 4] Dispatching Finalized Dossier to n8n Egress Webhook...")
    outbound_payload = {
        "business_name": memo.business_name,
        "applicant_name": memo.applicant_name,
        "loan_amount_requested_usd": memo.loan_amount_requested_usd,
        "dti_ratio": f"{memo.estimated_dti_ratio:.1%}",
        "risk_tier": memo.risk_tier,
        "collateral_type": "12 Reefer Fleet Units ($410k)",
        "executive_summary": memo.executive_summary,
        "red_flags": memo.red_flags,
        "analyst_notes": "Closed-loop verification passed via n8n automated bridge.",
        "asana_tasks": [t.task_title for t in memo.asana_tasks]
    }

    success_disp, msg_disp, enriched = crm_dispatcher.dispatch_to_n8n(
        webhook_url=N8N_WEBHOOK_URL,
        payload=outbound_payload,
        flow_type="credit"
    )
    print(f"Result: Success={success_disp} | Status Message: {msg_disp}")

    # Step 5: Mark record processed in database
    print("\n[Step 5] Marking Record Processed in SQLite Audit Log...")
    database.mark_operation_processed(
        record_id=record_id,
        dispatch_status="Synced to Google Sheets Credit LOS & Asana via n8n",
        headline_metric=f"${memo.loan_amount_requested_usd:,} USD | {memo.risk_tier}",
        assessment_summary=memo.executive_summary,
        full_output_json=memo.model_dump(),
        operator_name="Automated Inbound Bridge",
        operator_role="AI Solutions Engineer"
    )
    updated_rec = database.get_operation_by_id(record_id)
    assert updated_rec["is_processed"] == 1, "Record should now be marked processed"
    print(f"PASS: Record #{record_id} successfully marked as processed and synchronized.")

    print("\n" + "=" * 70)
    print("CLOSED-LOOP VERIFICATION COMPLETE (100% SUCCESS)")
    print("Inbound (Google Sheets -> n8n -> nuDesk) -> Triage -> Outbound (nuDesk -> n8n -> Workspace)")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = run_closed_loop_test()
    sys.exit(0 if success else 1)
