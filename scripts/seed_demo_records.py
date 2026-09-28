#!/usr/bin/env python3
"""
Pristine Demo Data Preparation Script
nuDesk Operations Studio — Mazatlán Talent Hub
Seeds clean, realistic pending operational files for live demonstration recording:
1. Credit: Apex Fleet Repair (Robert Martinez) — Equipment financing with verified DTI
2. Sales: Sunbelt Logistics LLC (Marcus Vance) — Factoring prospect with 30s script
3. HR: Valeria Beltrán — Senior Bilingual Underwriter candidate (C1)
"""
import sys
import os
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import database
from meeting_queue import (
    BENCHMARK_HR_TRANSCRIPT,
    BENCHMARK_SALES_LEAD,
    CARLOS_MENDOZA_TRANSCRIPT,
    VALERIA_BELTRAN_TRANSCRIPT
)
from mock_data import BENCHMARK_TRANSCRIPT


def prepare_pristine_demo_state():
    print("=" * 70)
    print("nuDesk Demo State Preparation")
    print("=" * 70)

    # 1. Credit Pending File
    c_id = database.ingest_pending_record(
        module_type="credit",
        entity_name="Apex Fleet Repair (Robert Martinez)",
        headline_metric="$85,000 USD | Equipment Term Loan",
        transcript_text=BENCHMARK_TRANSCRIPT,
        assessment_summary="Commercial fleet repair workshop in Phoenix, AZ seeking hydraulic bay expansion. Monthly revenue $38k. Active IRS installment verification required.",
        source_channel="Read AI (Google Meet Intake)",
        doc_url="https://drive.google.com/file/d/1B7x9_ApexFleet_Financials_2025.pdf",
        doc_note="Verified 6-month Chase operating bank statements + 2024 Form 1120-S",
        metadata_extra={"urgency": "High", "client_priority": "Priority 1"}
    )
    print(f" - [Credit Queue] Seeded pending loan file #{c_id}: Apex Fleet Repair")

    # 2. Sales Pending Lead
    s_id = database.ingest_pending_record(
        module_type="sales",
        entity_name="Sunbelt Logistics LLC (Marcus Vance)",
        headline_metric="$1,850,000 ARR | Freight Factoring",
        transcript_text=BENCHMARK_SALES_LEAD,
        assessment_summary="Interstate reefer carrier operating 14 power units across California and Arizona. Experiencing 45-day shipper payment lags during produce harvest surge.",
        source_channel="Fireflies.ai (Inbound Lead Call)",
        doc_url="https://drive.google.com/file/d/1S9v3_SunbeltLogistics_DOT_Audit.pdf",
        doc_note="Verified FMCSA Safer profile: active operating authority, satisfactory safety rating",
        metadata_extra={"fleet_size": 14, "target_market": "Cold-Chain Logistics"}
    )
    print(f" - [Sales Queue] Seeded pending commercial lead #{s_id}: Sunbelt Logistics LLC")

    # 3. HR Pending Candidate
    h_id = database.ingest_pending_record(
        module_type="hr",
        entity_name="Valeria Beltrán (Culiacán, Sin.)",
        headline_metric="Senior Commercial Underwriter (C1 Fluent)",
        transcript_text=VALERIA_BELTRAN_TRANSCRIPT,
        assessment_summary="Bilingual underwriting specialist with 5 years experience evaluating credit facilities and MCA risk for US logistics clients. C1 CEFR verified.",
        source_channel="Read AI (Screening Interview)",
        doc_url="https://app.read.ai/analytics/meetings/read_hr_77192_valeria",
        doc_note="LinkedIn verified, portfolio includes commercial underwriting memos and DTI debt analysis",
        metadata_extra={"applied_role": "Senior Commercial Underwriter", "target_hub": "Mazatlán"}
    )
    print(f" - [HR Queue] Seeded pending candidate scorecard #{h_id}: Valeria Beltrán")

    print("\n" + "=" * 70)
    print("Demo State Ready! All 3 queues have fresh pending files ready for camera.")
    print("=" * 70)


if __name__ == "__main__":
    prepare_pristine_demo_state()
