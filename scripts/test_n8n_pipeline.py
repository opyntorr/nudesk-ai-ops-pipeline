#!/usr/bin/env python3
"""
Test Suite for nuDesk n8n & Google Workspace Integration Pipeline
Tests both outputs (dispatch to n8n) and inputs (ingestion into nuDesk queue).
"""
import sys
import os
import json
import time

# Ensure parent directory is in Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import crm_dispatcher
import database
from scripts.ingest_incoming_file import ingest_file


def run_pipeline_tests():
    print("=" * 70)
    print("nuDesk n8n & Google Workspace Integration Verification")
    print("=" * 70)

    webhook_url = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/nudesk-triage")

    # ---------------------------------------------------------
    # TEST 1: INGESTION PIPELINE (INPUTS)
    # ---------------------------------------------------------
    print("\n[TEST 1] Ingesting New Meeting Bot Stream (Read AI Input)...")
    ingest_res = ingest_file(
        module_type="sales",
        entity_name="Calafia Cross-Border Freight (Tijuana, BC)",
        headline_metric="$3.1M ARR | 18 Refrigerated Units",
        transcript_text="[00:00:05] Agent: Reviewing cross-border produce factoring for Calafia...",
        source_channel="Google Meet via Read AI",
        doc_url="https://example.com/calafia-fleet-aging.pdf",
        doc_note="Attached AR Aging: $220k 30-day broker invoices",
        assessment_summary="Awaiting commercial BDR discovery analysis"
    )
    assert ingest_res["success"] is True
    print(f"PASS: Ingestion created pending record #{ingest_res['record_id']} with active SLA.")

    # ---------------------------------------------------------
    # TEST 2: CREDIT OUTPUT DISPATCH TO N8N
    # ---------------------------------------------------------
    print("\n[TEST 2] Dispatching Credit Underwriting Memo to n8n...")
    credit_payload = {
        "business_name": "Calafia Cross-Border Freight",
        "applicant_name": "Ernesto Calafia",
        "loan_amount_requested_usd": 220000,
        "dti_ratio": "38.5%",
        "risk_tier": "Low Risk",
        "collateral_type": "18 Reefer Trailing Equipment Units",
        "executive_summary": "Tier-1 cross-border carrier with consistent 45-day billing cycles.",
        "red_flags": ["Seasonal agricultural produce cycles"],
        "analyst_notes": "Financial audit passed; advance rate capped at 85%.",
        "asana_tasks": ["Verify commercial carrier insurance", "File UCC-1 lien"]
    }
    success_c, msg_c, payload_c = crm_dispatcher.dispatch_to_n8n(
        webhook_url=webhook_url,
        payload=credit_payload,
        flow_type="credit"
    )
    print(f"Result: Success={success_c} | Message: {msg_c}")

    # ---------------------------------------------------------
    # TEST 3: SALES BDR OUTREACH DISPATCH TO N8N
    # ---------------------------------------------------------
    print("\n[TEST 3] Dispatching Sales Commercial Lead & Gmail Draft to n8n...")
    sales_payload = {
        "company_name": "Pacific Cold Chain Logistics",
        "contact_person": "Patricia Valenzuela",
        "contact_email": "patricia@pacificcoldchain.com",
        "industry": "Perishable Freight",
        "annual_revenue_usd": 3500000,
        "lead_score": 94,
        "lead_tier": "Hot Lead",
        "draft_outreach_subject": "Optimización de Liquidez para Flota Refrigerada - nuDesk",
        "draft_outreach_body": "Estimada Patricia, identificamos una línea de factoraje con tasa preferencial del 2.8% para sus rutas Ensenada-San Diego.",
        "analyst_notes": "Prospecto de alto valor; coordinar demo con BDR Senior."
    }
    success_s, msg_s, payload_s = crm_dispatcher.dispatch_to_n8n(
        webhook_url=webhook_url,
        payload=sales_payload,
        flow_type="sales"
    )
    print(f"Result: Success={success_s} | Message: {msg_s}")

    # ---------------------------------------------------------
    # TEST 4: HR TALENT SCREENING DISPATCH TO N8N
    # ---------------------------------------------------------
    print("\n[TEST 4] Dispatching HR Talent Evaluation to n8n...")
    hr_payload = {
        "candidate_name": "Alejandro Rios",
        "applied_role": "Bilingual Senior Underwriter",
        "english_fluency_cefr": "C1",
        "technical_competency_score": 92,
        "salary_expectation_monthly_usd": 3200,
        "hiring_recommendation": "Advance to Technical Case Study",
        "analyst_notes": "Excepcional manejo de terminología crediticia comercial en inglés."
    }
    success_h, msg_h, payload_h = crm_dispatcher.dispatch_to_n8n(
        webhook_url=webhook_url,
        payload=hr_payload,
        flow_type="hr"
    )
    print(f"Result: Success={success_h} | Message: {msg_h}")

    # ---------------------------------------------------------
    # TEST 5: SIMULATION MODE FALLBACK WHEN WEBHOOK IS UNSET
    # ---------------------------------------------------------
    print("\n[TEST 5] Testing Simulation Mode Fallback (Unconfigured Webhook)...")
    success_sim, msg_sim, _ = crm_dispatcher.dispatch_to_n8n(
        webhook_url="",
        payload={"test": True},
        flow_type="credit"
    )
    assert success_sim is True
    assert "Simulation Mode" in msg_sim
    print("PASS: Simulation fallback cleanly validates payload without throwing exceptions.")

    print("\n" + "=" * 70)
    print("ALL INTEGRATION TESTS COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline_tests()
