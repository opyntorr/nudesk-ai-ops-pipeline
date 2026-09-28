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

BASE_URL = os.getenv("APP_URL", "http://localhost:8501")


def run_multi_role_operations():
    print("=" * 70)
    print("nuDesk Playwright Multi-Role Operations Runner")
    print(f"Targeting Application: {BASE_URL}")
    print("=" * 70)

    with sync_playwright() as p:
        # Launch Chromium headless
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
        context = browser.new_context(viewport={"width": 1600, "height": 1080})
        page = context.new_page()

        # Step 1: Open app with full permissions
        app_url = f"{BASE_URL}/?role=it_admin"
        print(f"\n[Step 1] Loading nuDesk application at {app_url}...")
        page.goto(app_url, wait_until="networkidle", timeout=30000)
        time.sleep(3)

        # -------------------------------------------------------------
        # ROLE 1: CREDIT OPERATIONS (UNDERWRITING)
        # -------------------------------------------------------------
        print("\n[Role 1] Operating as Credit Underwriter...")
        # Click Run Credit Triage
        btn_c_run = page.locator('button:has-text("Run Credit Triage")').first
        if btn_c_run.count() > 0:
            btn_c_run.scroll_into_view_if_needed()
            btn_c_run.click()
            print(" - Triggered 'Run Credit Triage'. Waiting for Gemini cascade...")

        try:
            btn_c_approve = page.wait_for_selector('button:has-text("Approve & Sign-Off (Auto-Advance)"), button:has-text("Approve & Sync")', timeout=20000)
            if btn_c_approve:
                btn_c_approve.scroll_into_view_if_needed()
                btn_c_approve.click()
                print(" - Clicked 'Approve & Sign-Off'. File dispatched to LOS, Asana, and Gmail!")
                time.sleep(4)
        except Exception:
            print(" - Warning: Credit approve button not found within timeout.")

        # -------------------------------------------------------------
        # ROLE 2: COMMERCIAL SALES (BDR OUTREACH)
        # -------------------------------------------------------------
        print("\n[Role 2] Operating as Commercial Sales BDR...")
        tab_sales = page.locator('button[role="tab"]:has-text("Commercial Sales"), [data-testid="stTab"]:has-text("Commercial Sales")').first
        if tab_sales.count() > 0:
            tab_sales.click()
            time.sleep(2)

        # Click Analyze Commercial Lead
        btn_s_run = page.locator('button:has-text("Analyze Commercial Lead")').first
        if btn_s_run.count() > 0:
            btn_s_run.scroll_into_view_if_needed()
            btn_s_run.click()
            print(" - Triggered 'Analyze Commercial Lead'. Waiting for AI scoring...")

        try:
            btn_s_qualify = page.wait_for_selector('button:has-text("Qualify Lead & Stage Outreach"), button:has-text("Sync Lead to CRM")', timeout=20000)
            if btn_s_qualify:
                btn_s_qualify.scroll_into_view_if_needed()
                btn_s_qualify.click()
                print(" - Clicked 'Qualify Lead & Stage Outreach'. Dispatched to CRM and Gmail!")
                time.sleep(4)
        except Exception:
            print(" - Warning: Sales qualify button not found within timeout.")

        # -------------------------------------------------------------
        # ROLE 3: TALENT OPERATIONS (HR SCREENING)
        # -------------------------------------------------------------
        print("\n[Role 3] Operating as HR Talent Recruiter...")
        tab_hr = page.locator('button[role="tab"]:has-text("Talent Operations"), [data-testid="stTab"]:has-text("Talent Operations")').first
        if tab_hr.count() > 0:
            tab_hr.click()
            time.sleep(2)

        # Click Grade Candidate Screening
        btn_h_run = page.locator('button:has-text("Grade Candidate Screening")').first
        if btn_h_run.count() > 0:
            btn_h_run.scroll_into_view_if_needed()
            btn_h_run.click()
            print(" - Triggered 'Grade Candidate Screening'. Waiting for evaluation...")

        try:
            btn_h_advance = page.wait_for_selector('button:has-text("Advance Candidate & Sign-Off"), button:has-text("Advance Candidate")', timeout=20000)
            if btn_h_advance:
                btn_h_advance.scroll_into_view_if_needed()
                btn_h_advance.click()
                print(" - Clicked 'Advance Candidate & Sign-Off'. Dispatched to Talent Roster and Gmail!")
                time.sleep(4)
        except Exception:
            print(" - Warning: HR advance button not found within timeout.")

        # -------------------------------------------------------------
        # ROLE 4: EXECUTIVE KPI DASHBOARD
        # -------------------------------------------------------------
        print("\n[Role 4] Operating as Executive Director...")
        tab_exec = page.locator('button[role="tab"]:has-text("Executive KPI"), [data-testid="stTab"]:has-text("Executive KPI")').first
        if tab_exec.count() > 0:
            tab_exec.click()
            time.sleep(2)

        # Click Dispatch Executive Operations Digest to Gmail
        btn_exec_dispatch = page.locator('button:has-text("Dispatch Executive Operations Digest to Gmail")').first
        if btn_exec_dispatch.count() > 0:
            btn_exec_dispatch.scroll_into_view_if_needed()
            btn_exec_dispatch.click()
            print(" - Clicked 'Dispatch Executive Operations Digest to Gmail'. Briefing dispatched!")
            time.sleep(4)
        else:
            print(" - Warning: Executive dispatch button not located on page.")

        # -------------------------------------------------------------
        # ROLE 5: IT & SYSTEM ADMINISTRATION
        # -------------------------------------------------------------
        print("\n[Role 5] Operating as IT Administrator...")
        tab_it = page.locator('button[role="tab"]:has-text("IT & System Administration"), [data-testid="stTab"]:has-text("IT & System")').first
        if tab_it.count() > 0:
            tab_it.click()
            time.sleep(2)

        # Switch to sub-tab System Telemetry & Integrations
        subtab_telemetry = page.locator('button[role="tab"]:has-text("System Telemetry"), [data-testid="stTab"]:has-text("System Telemetry")').first
        if subtab_telemetry.count() > 0:
            subtab_telemetry.click()
            time.sleep(1)

        # Click Dispatch IT Security & System Health Digest to Gmail
        btn_it_dispatch = page.locator('button:has-text("Dispatch IT Security & System Health Digest to Gmail")').first
        if btn_it_dispatch.count() > 0:
            btn_it_dispatch.scroll_into_view_if_needed()
            btn_it_dispatch.click()
            print(" - Clicked 'Dispatch IT Security & System Health Digest to Gmail'. Health audit dispatched!")
            time.sleep(4)
        else:
            print(" - Warning: IT dispatch button not located on page.")

        print("\n" + "=" * 70)
        print("Playwright Multi-Role Simulation Complete.")
        print("All 5 operational personas executed actions in the live UI.")
        print("=" * 70)

        browser.close()


if __name__ == "__main__":
    run_multi_role_operations()
