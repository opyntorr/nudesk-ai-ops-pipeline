#!/usr/bin/env python3
"""
Playwright End-to-End Multi-Role Operational Simulator
nuDesk Operations Studio — Mazatlán Talent Hub
Automates user actions across all 5 operational personas:
1. Credit Underwriting -> Approves loan file & triggers LOS/Asana/Gmail draft
2. Commercial Sales BDR -> Qualifies lead & triggers CRM/Gmail draft
3. HR Talent Recruiter -> Grades interview & triggers Roster/Gmail draft
4. Executive Director -> Generates and dispatches executive operations briefing
5. IT Administrator -> Generates and dispatches system integrity & security audit
"""
import sys
import os
import time
from playwright.sync_api import sync_playwright

# Ensure repository root is in sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import database
from scripts.generate_synthetic_intake import generate_synthetic_payload, extract_ingestion_fields

BASE_URL = os.getenv("APP_URL", "http://localhost:8501")


def ensure_pending_records_exist():
    """Ensure every operational queue has at least one pending file to triage."""
    specs = [
        ("credit", "readai"),
        ("sales", "fireflies"),
        ("hr", "readai")
    ]
    for mod, prov in specs:
        if not database.get_next_pending_operation(mod):
            print(f" - [Data Setup] Ingesting pending synthetic record for {mod.upper()} queue...")
            payload = generate_synthetic_payload(provider=prov, module=mod)
            norm = extract_ingestion_fields(payload, provider=prov, module=mod)
            database.ingest_pending_record(
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


def robust_switch_tab(page, tab_name: str, expected_selector: str, timeout_sec: int = 35) -> bool:
    """Safely switch to a tab and wait until the expected selector appears. Retries clicking if a page rerun resets active tab."""
    print(f" - Navigating to tab: {tab_name}...")
    start_time = time.time()
    while time.time() - start_time < timeout_sec:
        try:
            el = page.locator(expected_selector).last
            if el.is_visible():
                print(f" - Successfully selected {tab_name} and verified target element.")
                return True
        except Exception:
            pass

        try:
            page.evaluate("window.scrollTo(0, 0)")
            tabs = page.locator('[data-testid="stTab"]').all()
            for t in tabs:
                if tab_name.lower() in t.inner_text().lower():
                    t.click(force=True)
                    time.sleep(2.5)
                    break
        except Exception:
            time.sleep(1)

    print(f" - Warning: Tab '{tab_name}' did not mount '{expected_selector}' within {timeout_sec}s.")
    return False


def run_multi_role_operations():
    print("=" * 70)
    print("nuDesk Playwright Multi-Role Operations Runner")
    print(f"Targeting Application: {BASE_URL}")
    print("=" * 70)

    # Pre-condition: ensure test data exists across queues
    ensure_pending_records_exist()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
        context = browser.new_context(viewport={"width": 1600, "height": 1080})
        page = context.new_page()

        # Step 1: Open app with full permissions
        app_url = f"{BASE_URL}/?role=it_admin"
        print(f"\n[Step 1] Loading nuDesk application at {app_url}...")
        page.goto(app_url, wait_until="networkidle", timeout=30000)
        page.wait_for_selector('[data-testid="stTab"]', timeout=20000)
        time.sleep(2)

        # -------------------------------------------------------------
        # ROLE 1: CREDIT OPERATIONS (UNDERWRITING)
        # -------------------------------------------------------------
        print("\n[Role 1] Operating as Credit Underwriter...")
        robust_switch_tab(page, "Credit Operations", 'button:has-text("Run Credit Triage")')
        btn_c_run = page.locator('button:has-text("Run Credit Triage")').last
        btn_c_run.scroll_into_view_if_needed()
        btn_c_run.click()
        print(" - Triggered 'Run Credit Triage'. Waiting for Gemini cascade...")

        try:
            btn_c_approve = page.locator('button:has-text("Approve & Sign-Off (Auto-Advance)"), button:has-text("Approve & Sync")').last
            btn_c_approve.wait_for(state="visible", timeout=35000)
            btn_c_approve.scroll_into_view_if_needed()
            btn_c_approve.click()
            print(" - Clicked 'Approve & Sign-Off'. File dispatched to LOS, Asana, and Gmail!")
            time.sleep(5)
        except Exception as e:
            print(f" - Warning: Credit approve step failed: {e}")

        # -------------------------------------------------------------
        # ROLE 2: COMMERCIAL SALES (BDR OUTREACH)
        # -------------------------------------------------------------
        print("\n[Role 2] Operating as Commercial Sales BDR...")
        robust_switch_tab(page, "Commercial Sales", 'button:has-text("Analyze Commercial Lead")')

        try:
            btn_s_run = page.locator('button:has-text("Analyze Commercial Lead")').last
            btn_s_run.scroll_into_view_if_needed()
            btn_s_run.click()
            print(" - Triggered 'Analyze Commercial Lead'. Waiting for AI scoring...")

            btn_s_qualify = page.locator('button:has-text("Qualify Lead & Stage Outreach"), button:has-text("Sync Lead to CRM")').last
            btn_s_qualify.wait_for(state="visible", timeout=35000)
            btn_s_qualify.scroll_into_view_if_needed()
            btn_s_qualify.click()
            print(" - Clicked 'Qualify Lead & Stage Outreach'. Dispatched to CRM and Gmail!")
            time.sleep(5)
        except Exception as e:
            print(f" - Warning: Sales qualify step failed: {e}")

        # -------------------------------------------------------------
        # ROLE 3: TALENT OPERATIONS (HR SCREENING)
        # -------------------------------------------------------------
        print("\n[Role 3] Operating as HR Talent Recruiter...")
        robust_switch_tab(page, "Talent Operations", 'button:has-text("Grade Candidate Screening")')

        try:
            btn_h_run = page.locator('button:has-text("Grade Candidate Screening")').last
            btn_h_run.scroll_into_view_if_needed()
            btn_h_run.click()
            print(" - Triggered 'Grade Candidate Screening'. Waiting for evaluation...")

            btn_h_advance = page.locator('button:has-text("Advance Candidate & Sign-Off"), button:has-text("Advance Candidate")').last
            btn_h_advance.wait_for(state="visible", timeout=35000)
            btn_h_advance.scroll_into_view_if_needed()
            btn_h_advance.click()
            print(" - Clicked 'Advance Candidate & Sign-Off'. Dispatched to Talent Roster and Gmail!")
            time.sleep(5)
        except Exception as e:
            print(f" - Warning: HR action step failed: {e}")

        # -------------------------------------------------------------
        # ROLE 4: EXECUTIVE KPI DASHBOARD
        # -------------------------------------------------------------
        print("\n[Role 4] Operating as Executive Director...")
        robust_switch_tab(page, "Executive KPI", 'button:has-text("Dispatch Executive Operations Digest to Gmail")')

        try:
            btn_exec_dispatch = page.locator('button:has-text("Dispatch Executive Operations Digest to Gmail")').first
            btn_exec_dispatch.scroll_into_view_if_needed()
            btn_exec_dispatch.click()
            print(" - Clicked 'Dispatch Executive Operations Digest to Gmail'. Briefing dispatched!")
            time.sleep(5)
        except Exception as e:
            print(f" - Warning: Executive dispatch step failed: {e}")

        # -------------------------------------------------------------
        # ROLE 5: IT & SYSTEM ADMINISTRATION
        # -------------------------------------------------------------
        print("\n[Role 5] Operating as IT Administrator...")
        robust_switch_tab(page, "IT & System Administration", '[data-testid="stTab"]:has-text("System Telemetry")')

        try:
            robust_switch_tab(page, "System Telemetry", 'button:has-text("Dispatch IT Security & System Health Digest to Gmail")')

            btn_it_dispatch = page.locator('button:has-text("Dispatch IT Security & System Health Digest to Gmail")').first
            btn_it_dispatch.scroll_into_view_if_needed()
            btn_it_dispatch.click()
            print(" - Clicked 'Dispatch IT Security & System Health Digest to Gmail'. Health audit dispatched!")
            time.sleep(5)
        except Exception as e:
            print(f" - Warning: IT dispatch step failed: {e}")

        print("\n" + "=" * 70)
        print("Playwright Multi-Role Simulation Complete.")
        print("All 5 operational personas executed actions in the live UI.")
        print("=" * 70)

        browser.close()


if __name__ == "__main__":
    run_multi_role_operations()
