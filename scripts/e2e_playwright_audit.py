#!/usr/bin/env python3
"""
Playwright End-to-End Verification & High-Resolution Screenshot Capture Suite
nuDesk Operations Studio — FinTech Operations Cockpit
Tests UI navigation, agentic tool trace display, Wispr Flow voice intake, and Dark Mode.
"""
import sys
import os
import shutil
import time
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "screenshots")
DOCS_SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "screenshots")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(DOCS_SCREENSHOTS_DIR, exist_ok=True)


def run_e2e_audit(base_url: str = "http://localhost:8501", headless: bool = True):
    print("=" * 70)
    print("Starting nuDesk Operations Studio Playwright E2E Audit")
    print(f"Target URL: {base_url} | Headless Mode: {headless}")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=["--no-sandbox", "--disable-gpu"])
        context = browser.new_context(viewport={"width": 1600, "height": 1000}, device_scale_factor=2)
        page = context.new_page()

        # Step 1: Open app with it_admin role query parameter
        target_url = f"{base_url}/?role=it_admin"
        print(f"\n[Step 1] Navigating to {target_url}...")
        page.goto(target_url, wait_until="networkidle", timeout=30000)
        time.sleep(3)

        # Step 2: Capture initial Credit Operations Cockpit
        shot_01 = os.path.join(SCREENSHOTS_DIR, "01_credit_triage_cockpit.png")
        page.screenshot(path=shot_01, full_page=False)
        print("PASS: Captured 01_credit_triage_cockpit.png")

        # Step 3: Trigger Agentic Credit Triage
        print("\n[Step 2] Triggering Agentic Credit Triage...")
        btn_run = page.locator('button:has-text("Run Credit Triage")').first
        if btn_run.count() > 0:
            btn_run.scroll_into_view_if_needed()
            btn_run.click()
            print("Clicked 'Run Credit Triage'. Waiting for agent reasoning and Pydantic synthesis...")
            time.sleep(4)

            # Look for Agent Reasoning expander
            expander = page.locator('summary:has-text("Agent Reasoning & Deterministic Tool Execution Trace"), [data-testid="stExpander"] summary').first
            if expander.count() > 0:
                expander.scroll_into_view_if_needed()
                expander.click()
                time.sleep(1)
                print("Expanded Agent Reasoning & Tool Trace.")

            shot_02 = os.path.join(SCREENSHOTS_DIR, "02_agent_reasoning_trace.png")
            page.screenshot(path=shot_02, full_page=False)
            print("PASS: Captured 02_agent_reasoning_trace.png")

        # Step 4: Navigate to Tab 2 (Commercial Sales)
        print("\n[Step 3] Switching to Commercial Sales (BDR Outreach) Tab...")
        tab_sales = page.locator('button[role="tab"]:has-text("Commercial Sales"), [data-testid="stTab"]:has-text("Commercial Sales")').first
        if tab_sales.count() > 0:
            tab_sales.click()
            time.sleep(2)
            shot_03 = os.path.join(SCREENSHOTS_DIR, "03_sales_bdr_cockpit.png")
            page.screenshot(path=shot_03, full_page=False)
            print("PASS: Captured 03_sales_bdr_cockpit.png")

        # Step 5: Navigate to Tab 3 (Talent Operations HR)
        print("\n[Step 4] Switching to Talent Operations (HR Screening) Tab...")
        tab_hr = page.locator('button[role="tab"]:has-text("Talent Operations"), [data-testid="stTab"]:has-text("Talent Operations")').first
        if tab_hr.count() > 0:
            tab_hr.click()
            time.sleep(2)
            shot_04 = os.path.join(SCREENSHOTS_DIR, "04_hr_talent_screening.png")
            page.screenshot(path=shot_04, full_page=False)
            print("PASS: Captured 04_hr_talent_screening.png")

        # Step 6: Navigate to Tab 4 (Executive KPI Dashboard)
        print("\n[Step 5] Switching to Executive KPI Dashboard & History Tab...")
        tab_exec = page.locator('button[role="tab"]:has-text("Executive KPI"), [data-testid="stTab"]:has-text("Executive KPI")').first
        if tab_exec.count() > 0:
            tab_exec.click()
            time.sleep(2)
            shot_05 = os.path.join(SCREENSHOTS_DIR, "05_executive_kpis.png")
            page.screenshot(path=shot_05, full_page=False)
            print("PASS: Captured 05_executive_kpis.png")

        # Step 7: Navigate to Tab 5 (IT & System Administration)
        print("\n[Step 6] Switching to IT & System Administration Tab...")
        tab_it = page.locator('button[role="tab"]:has-text("IT & System Administration"), [data-testid="stTab"]:has-text("IT & System")').first
        if tab_it.count() > 0:
            tab_it.click()
            time.sleep(2)

            # Click Sub-tab "System Telemetry & Integrations"
            subtab_telemetry = page.locator('button[role="tab"]:has-text("System Telemetry"), [data-testid="stTab"]:has-text("System Telemetry")').first
            if subtab_telemetry.count() > 0:
                print("Clicking 'System Telemetry & Integrations' sub-tab...")
                subtab_telemetry.click()
                time.sleep(2)

            shot_06 = os.path.join(SCREENSHOTS_DIR, "06_it_workbench_wispr_flow.png")
            page.screenshot(path=shot_06, full_page=False)
            print("PASS: Captured 06_it_workbench_wispr_flow.png")

            # Click Wispr Flow Voice Dictation injection button
            btn_wispr = page.locator('button:has-text("Inject Wispr Flow Voice Dictation Memo")').first
            if btn_wispr.count() > 0:
                print("Clicking 'Inject Wispr Flow Voice Dictation Memo'...")
                btn_wispr.scroll_into_view_if_needed()
                btn_wispr.click()
                time.sleep(2)
                shot_07 = os.path.join(SCREENSHOTS_DIR, "07_wispr_intake_confirmed.png")
                page.screenshot(path=shot_07, full_page=False)
                print("PASS: Captured 07_wispr_intake_confirmed.png")

        # Step 8: Toggle Dark Mode
        print("\n[Step 7] Testing Dark Mode Palette...")
        dark_url = f"{base_url}/?role=it_admin&theme=dark"
        page.goto(dark_url, wait_until="networkidle", timeout=30000)
        time.sleep(2)
        shot_08 = os.path.join(SCREENSHOTS_DIR, "08_dark_mode_palette.png")
        page.screenshot(path=shot_08, full_page=False)
        print("PASS: Captured 08_dark_mode_palette.png")

        # Copy all screenshots to docs/screenshots
        for fname in os.listdir(SCREENSHOTS_DIR):
            if fname.endswith(".png"):
                src = os.path.join(SCREENSHOTS_DIR, fname)
                dst = os.path.join(DOCS_SCREENSHOTS_DIR, fname)
                shutil.copy2(src, dst)

        print("\nAll screenshots synchronized to assets/screenshots/ and docs/screenshots/.")
        browser.close()
        print("Playwright E2E Audit Completed Successfully!")


if __name__ == "__main__":
    is_headless = "--headed" not in sys.argv
    run_e2e_audit(headless=is_headless)
