#!/usr/bin/env python3
"""
Multi-Device Visual Evidence Capture Suite
nuDesk Operations Studio - FinTech Operations Cockpit
Captures high-resolution screenshots for Android Mobile (Pixel 7) and Mac Desktop.
"""
import os
import shutil
import time
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "screenshots")
DOCS_DIR = os.path.join(BASE_DIR, "docs", "screenshots")

os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)


def capture_all(base_url: str = "http://localhost:8501"):
    print("=" * 70)
    print("Starting Multi-Device Screenshot Generation (Android Mobile & Mac Desktop)")
    print(f"Target URL: {base_url}")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])

        # -------------------------------------------------------------
        # 1. ANDROID MOBILE EMULATION (Google Pixel 7)
        # -------------------------------------------------------------
        print("\n[Phase 1] Emulating Android Device (Google Pixel 7)...")
        pixel_descriptor = p.devices["Pixel 7"]
        mobile_context = browser.new_context(
            **pixel_descriptor
        )
        mobile_page = mobile_context.new_page()

        # Shot 1: Mobile Credit Cockpit (Top View)
        url_credit = f"{base_url}/?role=credit_underwriter"
        print(f"Navigating to {url_credit}...")
        mobile_page.goto(url_credit, wait_until="networkidle", timeout=30000)
        time.sleep(3)

        shot_mob_credit = os.path.join(ASSETS_DIR, "mobile_android_credit_cockpit.png")
        mobile_page.screenshot(path=shot_mob_credit, full_page=False)
        print("Captured mobile_android_credit_cockpit.png")

        # Shot 2: Mobile Credit Underwriting Dossier (Run Triage)
        print("Running Credit Triage on mobile...")
        btn_run = mobile_page.locator('button:has-text("Run Credit Triage")').first
        if btn_run.count() > 0:
            btn_run.scroll_into_view_if_needed()
            btn_run.click()
            mobile_page.wait_for_selector('text=Executive Underwriting Memo', timeout=30000)
            time.sleep(2)
            memo = mobile_page.locator('text=Executive Underwriting Memo').first
            memo.scroll_into_view_if_needed()
            time.sleep(1)
            shot_mob_dossier = os.path.join(ASSETS_DIR, "mobile_android_credit_dossier.png")
            mobile_page.screenshot(path=shot_mob_dossier, full_page=False)
            print("Captured mobile_android_credit_dossier.png")

        # Shot 3: Mobile Commercial Sales (BDR Outreach)
        print("Switching to Commercial Sales Tab on mobile...")
        tab_sales = mobile_page.locator('button[role="tab"]:has-text("Commercial Sales"), [data-testid="stTab"]:has-text("Commercial Sales")').first
        if tab_sales.count() > 0:
            tab_sales.click()
            time.sleep(3)
            shot_mob_sales = os.path.join(ASSETS_DIR, "mobile_android_sales_cockpit.png")
            mobile_page.screenshot(path=shot_mob_sales, full_page=False)
            print("Captured mobile_android_sales_cockpit.png")

        # Shot 4: Mobile Executive KPI Dashboard
        print("Switching to Executive KPI Tab on mobile...")
        tab_exec = mobile_page.locator('button[role="tab"]:has-text("Executive KPI"), [data-testid="stTab"]:has-text("Executive KPI")').first
        if tab_exec.count() > 0:
            tab_exec.click()
            time.sleep(3)
            shot_mob_exec = os.path.join(ASSETS_DIR, "mobile_android_exec_dashboard.png")
            mobile_page.screenshot(path=shot_mob_exec, full_page=False)
            print("Captured mobile_android_exec_dashboard.png")

        mobile_context.close()

        # -------------------------------------------------------------
        # 2. MAC DESKTOP EMULATION (MacBook Pro Safari / Chrome)
        # -------------------------------------------------------------
        print("\n[Phase 2] Emulating Mac Desktop View (MacBook Pro 1600x1000)...")
        mac_context = browser.new_context(
            viewport={"width": 1600, "height": 1000},
            device_scale_factor=2,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        mac_page = mac_context.new_page()

        # Shot 5: Mac Credit Operations Workspace
        url_mac_admin = f"{base_url}/?role=it_admin"
        print(f"Navigating to {url_mac_admin}...")
        mac_page.goto(url_mac_admin, wait_until="networkidle", timeout=30000)
        time.sleep(3)

        shot_mac_credit = os.path.join(ASSETS_DIR, "desktop_mac_credit_underwriting.png")
        mac_page.screenshot(path=shot_mac_credit, full_page=False)
        print("Captured desktop_mac_credit_underwriting.png")

        # Shot 6: Mac Executive Operations Digest
        print("Navigating to Executive KPI Tab on Mac...")
        tab_mac_exec = mac_page.locator('button[role="tab"]:has-text("Executive KPI"), [data-testid="stTab"]:has-text("Executive KPI")').first
        if tab_mac_exec.count() > 0:
            tab_mac_exec.click()
            time.sleep(3)
            shot_mac_exec = os.path.join(ASSETS_DIR, "desktop_mac_executive_digest.png")
            mac_page.screenshot(path=shot_mac_exec, full_page=False)
            print("Captured desktop_mac_executive_digest.png")

        # Shot 7: Mac IT System Governance Workbench
        print("Navigating to IT & System Administration Tab on Mac...")
        tab_mac_it = mac_page.locator('button[role="tab"]:has-text("IT & System Administration"), [data-testid="stTab"]:has-text("IT & System")').first
        if tab_mac_it.count() > 0:
            tab_mac_it.click()
            time.sleep(3)
            shot_mac_it = os.path.join(ASSETS_DIR, "desktop_mac_it_governance.png")
            mac_page.screenshot(path=shot_mac_it, full_page=False)
            print("Captured desktop_mac_it_governance.png")

        mac_context.close()
        browser.close()

        # Synchronize all screenshots to docs/screenshots
        print("\nSynchronizing screenshots to docs/screenshots/...")
        for fname in os.listdir(ASSETS_DIR):
            if fname.endswith(".png"):
                src = os.path.join(ASSETS_DIR, fname)
                dst = os.path.join(DOCS_DIR, fname)
                shutil.copy2(src, dst)
        print("All screenshots successfully synchronized.")


if __name__ == "__main__":
    capture_all()
