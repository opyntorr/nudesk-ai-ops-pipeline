"""
SQLite Persistence Layer for nuDesk Operations Studio
nuDesk MX — Mazatlán Operations Hub & US Commercial Lending
Provides persistent audit trails, operational history, dual-queue triage, and multi-criteria queries.
"""
import os
import sqlite3
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "operations_history.db")


def get_connection() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS operations_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            operator_name TEXT NOT NULL,
            operator_role TEXT NOT NULL,
            module_type TEXT NOT NULL,
            entity_name TEXT NOT NULL,
            headline_metric TEXT NOT NULL,
            assessment_summary TEXT NOT NULL,
            full_output_json TEXT NOT NULL,
            dispatch_status TEXT NOT NULL,
            is_processed INTEGER DEFAULT 1,
            source_channel TEXT DEFAULT 'Google Meet / Read AI'
        )
    """)
    conn.commit()

    # Schema migration if table already existed without is_processed, source_channel, or analyst_notes
    cursor.execute("PRAGMA table_info(operations_history)")
    existing_cols = [row["name"] for row in cursor.fetchall()]
    if "is_processed" not in existing_cols:
        cursor.execute("ALTER TABLE operations_history ADD COLUMN is_processed INTEGER DEFAULT 1")
    if "source_channel" not in existing_cols:
        cursor.execute("ALTER TABLE operations_history ADD COLUMN source_channel TEXT DEFAULT 'Google Meet / Read AI'")
    if "analyst_notes" not in existing_cols:
        cursor.execute("ALTER TABLE operations_history ADD COLUMN analyst_notes TEXT DEFAULT ''")
    conn.commit()

    # Clean legacy dummy test records
    cursor.execute("DELETE FROM operations_history WHERE entity_name LIKE '%Test Enterprise%' OR entity_name LIKE '%Benchmark Enterprise%' OR operator_name = 'Unit Test Operator'")
    conn.commit()

    # Seed organic benchmarks if database is freshly initialized or empty
    cursor.execute("SELECT COUNT(*) as count FROM operations_history")
    total_count = cursor.fetchone()["count"]
    if total_count == 0:
        seed_organic_benchmarks(conn)

    conn.close()


def save_operation(
    operator_name: str,
    operator_role: str,
    module_type: str,
    entity_name: str,
    headline_metric: str,
    assessment_summary: str,
    full_output_json: Dict[str, Any],
    dispatch_status: str = "Synced",
    is_processed: int = 1,
    source_channel: str = "Google Meet / Read AI",
    analyst_notes: str = ""
) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    cursor.execute("""
        INSERT INTO operations_history (
            timestamp, operator_name, operator_role, module_type,
            entity_name, headline_metric, assessment_summary,
            full_output_json, dispatch_status, is_processed, source_channel, analyst_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        operator_name,
        operator_role,
        module_type,
        entity_name,
        headline_metric,
        assessment_summary,
        json.dumps(full_output_json, ensure_ascii=False),
        dispatch_status,
        is_processed,
        source_channel,
        analyst_notes
    ))
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id


def mark_operation_processed(
    record_id: int,
    dispatch_status: str = "Synced",
    headline_metric: Optional[str] = None,
    assessment_summary: Optional[str] = None,
    full_output_json: Optional[Dict[str, Any]] = None,
    operator_name: Optional[str] = None,
    operator_role: Optional[str] = None,
    analyst_notes: Optional[str] = None
) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    updates = ["is_processed = 1", "dispatch_status = ?"]
    params: List[Any] = [dispatch_status]

    if headline_metric is not None:
        updates.append("headline_metric = ?")
        params.append(headline_metric)
    if assessment_summary is not None:
        updates.append("assessment_summary = ?")
        params.append(assessment_summary)
    if full_output_json is not None:
        updates.append("full_output_json = ?")
        params.append(json.dumps(full_output_json, ensure_ascii=False))
    if operator_name is not None:
        updates.append("operator_name = ?")
        params.append(operator_name)
    if operator_role is not None:
        updates.append("operator_role = ?")
        params.append(operator_role)
    if analyst_notes is not None:
        updates.append("analyst_notes = ?")
        params.append(analyst_notes)

    updates.append("timestamp = ?")
    params.append(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

    params.append(record_id)
    cursor.execute(f"UPDATE operations_history SET {', '.join(updates)} WHERE id = ?", tuple(params))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


def get_filtered_operations(
    module_filter: str = "all",
    search_query: str = "",
    sort_by: str = "date",
    sort_order: str = "desc",
    status_filter: str = "all",
    time_window: str = "week",
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Retrieve operational logs with multi-field search, status filtering,
    time-window bounding, and dynamic SQL ordering.
    """
    conn = get_connection()
    cursor = conn.cursor()

    conditions = []
    params: List[Any] = []

    # Module filter
    if module_filter and module_filter.lower() != "all":
        conditions.append("module_type = ?")
        params.append(module_filter.lower())

    # Processing status filter (unprocessed / pending vs processed / synced)
    if status_filter == "pending":
        conditions.append("is_processed = 0")
    elif status_filter == "processed":
        conditions.append("is_processed = 1")

    # Time window filter (default: rolling 7 days)
    now = datetime.now()
    if time_window == "today":
        cutoff = now.strftime("%Y-%m-%d 00:00:00")
        conditions.append("timestamp >= ?")
        params.append(cutoff)
    elif time_window == "week":
        cutoff = (now - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        conditions.append("timestamp >= ?")
        params.append(cutoff)
    elif time_window == "month":
        cutoff = (now - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")
        conditions.append("timestamp >= ?")
        params.append(cutoff)
    # 'all' applies no timestamp cutoff

    # Partial keyword search
    if search_query and search_query.strip():
        term = f"%{search_query.strip()}%"
        conditions.append(
            "(entity_name LIKE ? OR operator_name LIKE ? OR headline_metric LIKE ? OR assessment_summary LIKE ? OR source_channel LIKE ?)"
        )
        params.extend([term, term, term, term, term])

    query = "SELECT * FROM operations_history"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    # Dynamic Sorting
    direction = "ASC" if sort_order.lower() == "asc" else "DESC"
    if sort_by == "name":
        query += f" ORDER BY entity_name COLLATE NOCASE {direction}"
    elif sort_by == "metric":
        query += f" ORDER BY headline_metric COLLATE NOCASE {direction}"
    elif sort_by == "operator":
        query += f" ORDER BY operator_name COLLATE NOCASE {direction}"
    else:  # date
        query += f" ORDER BY timestamp {direction}"

    query += " LIMIT ?"
    params.append(limit)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results


def get_operations(limit: int = 50, module_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Legacy backward-compatible wrapper."""
    return get_filtered_operations(module_filter=module_type or "all", limit=limit, time_window="all")


def get_department_kpis(module_type: str, time_window: str = "week") -> Dict[str, Any]:
    """Calculate executive metrics for a specific department."""
    records = get_filtered_operations(module_filter=module_type, status_filter="all", time_window=time_window, limit=500)
    pending = [r for r in records if r["is_processed"] == 0]
    processed = [r for r in records if r["is_processed"] == 1]
    return {
        "total": len(records),
        "pending_count": len(pending),
        "processed_count": len(processed),
        "records": records,
        "pending": pending,
        "processed": processed
    }


def calculate_sla_status(timestamp_str: str, is_processed: int = 0) -> Dict[str, str]:
    """Calculate elapsed SLA and badge category for triage items."""
    try:
        record_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        elapsed = datetime.now() - record_time
        mins = max(0, int(elapsed.total_seconds() / 60))

        if mins < 60:
            time_label = f"{mins}m ago"
        elif mins < 1440:
            hrs = int(mins / 60)
            time_label = f"{hrs}h {mins % 60}m ago"
        else:
            days = int(mins / 1440)
            time_label = f"{days}d ago"

        if is_processed == 1:
            return {"label": time_label, "tier": "SYNCED", "color": "badge-green"}
        if mins > 120:
            return {"label": f"SLA {time_label}", "tier": "BREACH", "color": "badge-red"}
        elif mins > 30:
            return {"label": time_label, "tier": "ATTENTION", "color": "badge-teal"}
        return {"label": time_label, "tier": "NEW", "color": "badge-green"}
    except Exception:
        return {"label": timestamp_str, "tier": "NORMAL", "color": "badge-navy"}


def get_next_pending_operation(module_type: str, exclude_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Retrieve the next oldest pending operation in FIFO order to auto-advance."""
    conn = get_connection()
    cursor = conn.cursor()
    if exclude_id is not None:
        cursor.execute("""
            SELECT * FROM operations_history
            WHERE module_type = ? AND is_processed = 0 AND id != ?
            ORDER BY timestamp ASC LIMIT 1
        """, (module_type.lower(), exclude_id))
    else:
        cursor.execute("""
            SELECT * FROM operations_history
            WHERE module_type = ? AND is_processed = 0
            ORDER BY timestamp ASC LIMIT 1
        """, (module_type.lower(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_operation_by_id(record_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single operation by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM operations_history WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def seed_organic_benchmarks(conn: sqlite3.Connection) -> None:
    """
    Seed realistic Mazatlán operations activity for US commercial debt and recruiting.
    Includes both Unprocessed (Pending Intake) and Processed (Synced to System) records.
    """
    now = datetime.now()
    t_minus = lambda minutes: (now - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
    t_minus_hours = lambda hours: (now - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    t_minus_days = lambda days: (now - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    organic_records = [
        # -------------------------------------------------------------
        # PENDING INTAKE QUEUE (UNPROCESSED - FIFO Priority)
        # -------------------------------------------------------------
        (
            t_minus(8),
            "Unassigned (Intake Queue)",
            "Incoming Stream",
            "credit",
            "Apex Fleet Repair (Dallas, TX)",
            "$85,000 USD | Equipment Term Loan",
            "Owner Robert Martinez seeking hydraulic lift financing. $38k monthly revenue. Verified tax lien installment in place.",
            json.dumps({"requested_amount": 85000, "collateral": "Rotary Lift Heavy Hydraulic", "status": "pending_triage", "dti": 0.28, "risk_tier": "Low Risk"}),
            "Pending Triage",
            0,
            "Google Meet via Read AI",
            ""
        ),
        (
            t_minus(42),
            "Unassigned (Intake Queue)",
            "Incoming Stream",
            "credit",
            "Gulf Coast Marine Welding (Galveston, TX)",
            "$140,000 USD | Working Capital Line",
            "Shipyard subcontractor needing weekly payroll float against verified 45-day marine repair contracts. No UCC liens.",
            json.dumps({"requested_amount": 140000, "collateral": "Commercial Receivables", "status": "pending_triage", "dti": 0.31, "risk_tier": "Low Risk"}),
            "Pending Triage",
            0,
            "Google Meet via Fireflies.ai",
            ""
        ),
        (
            t_minus_hours(3),
            "Unassigned (Intake Queue)",
            "Incoming Stream",
            "credit",
            "Rio Grande Distribution (Laredo, TX)",
            "$210,000 USD | Freight Factoring",
            "Cross-border carrier with 18 refrigerated trailers. 55-day broker payment terms. High intent for spot factoring line.",
            json.dumps({"requested_amount": 210000, "collateral": "Freight Invoices", "status": "pending_triage", "dscr": 1.42, "risk_tier": "Low Risk"}),
            "Pending Triage",
            0,
            "Google Meet via Read AI",
            ""
        ),
        (
            t_minus_hours(5),
            "Robert Martinez",
            "Senior Underwriter",
            "credit",
            "Red River Heavy Fabrication (Tulsa, OK)",
            "$220,000 USD | CNC Machinery Expansion",
            "High revenue volatility ($110k - $24k/mo); multiple active MCA daily debit positions detected on bank statements.",
            json.dumps({"risk_tier": "High Risk", "requested_amount": 220000, "mca_stacking_detected": True, "collateral": "CNC Machinery"}),
            "Pending Triage",
            0,
            "Google Meet via Read AI",
            "Requires senior underwriter exception approval due to existing MCA liens."
        ),
        (
            t_minus(22),
            "Unassigned (Intake Queue)",
            "Incoming Stream",
            "sales",
            "Sunbelt Logistics LLC (Phoenix, AZ)",
            "$2.4M ARR | 14 Tractor Fleet",
            "Marcus Vance (Managing Director) requesting 90-day freight billing line. Urgent liquidity need for driver recruitment.",
            json.dumps({"arr": 2400000, "fleet_size": 14, "lead_score": 92, "status": "pending_lead_qualification"}),
            "Pending Triage",
            0,
            "Google Meet via Fireflies.ai",
            ""
        ),
        (
            t_minus_hours(1),
            "Unassigned (Intake Queue)",
            "Incoming Stream",
            "sales",
            "Baja Cross-Border Cold Chain (Otay Mesa, CA)",
            "$1.6M ARR | 8 Refrigerated Reefers",
            "Diana Navarro seeking non-recourse factoring line for perishable produce shipments across Tijuana-San Diego corridor.",
            json.dumps({"arr": 1600000, "fleet_size": 8, "lead_score": 86, "status": "pending_lead_qualification"}),
            "Pending Triage",
            0,
            "Google Meet via Read AI",
            ""
        ),
        (
            t_minus_hours(4),
            "Unassigned (Intake Queue)",
            "Incoming Stream",
            "sales",
            "Alamo Industrial Coatings (San Antonio, TX)",
            "$980,000 ARR | Municipal Painting",
            "Jorge Villarreal requesting progress billing advance against municipal water tower rehabilitation project.",
            json.dumps({"arr": 980000, "fleet_size": 4, "lead_score": 79, "status": "pending_lead_qualification"}),
            "Pending Triage",
            0,
            "Google Meet via Read AI",
            ""
        ),
        (
            t_minus(35),
            "Unassigned (Intake Queue)",
            "Incoming Stream",
            "hr",
            "Sofia Valdez (Mazatlán, Sin.)",
            "High Fit (94) | Psico: 92 | Test: 96",
            "Screening call with Elena Ramos. 4 years SME underwriting experience; demonstrated sharp detection of undisclosed MCA debt.",
            json.dumps({
                "candidate": "Sofia Valdez",
                "applied_role": "Senior Bilingual Credit Analyst",
                "application_area": "Credit Underwriting & Risk",
                "candidate_fit_tier": "High Fit",
                "candidate_fit_score": 94,
                "psychometrics_score": 92,
                "knowledge_test_score": 96,
                "overall_fit_score": 94,
                "experience_years": 4,
                "cefr": "C1",
                "action": "Advance to Interview"
            }),
            "Pending Triage",
            0,
            "Google Meet via Read AI",
            ""
        ),
        (
            t_minus_hours(2),
            "Unassigned (Intake Queue)",
            "Incoming Stream",
            "hr",
            "Carlos Mendoza (Mazatlán, Sin.)",
            "High Fit (87) | Psico: 89 | Test: 88",
            "3 years outbound B2B sales experience targeting US logistics carriers. Fluent commercial English with confident objection handling.",
            json.dumps({
                "candidate": "Carlos Mendoza",
                "applied_role": "Commercial BDR (Logistics)",
                "application_area": "Commercial Sales & BDR",
                "candidate_fit_tier": "High Fit",
                "candidate_fit_score": 87,
                "psychometrics_score": 89,
                "knowledge_test_score": 88,
                "overall_fit_score": 87,
                "experience_years": 3,
                "cefr": "B2+",
                "action": "Advance to Case Study"
            }),
            "Pending Triage",
            0,
            "Google Meet via Read AI",
            ""
        ),
        (
            t_minus_hours(6),
            "Unassigned (Intake Queue)",
            "Incoming Stream",
            "hr",
            "Valeria Beltrán (Culiacán, Sin.)",
            "High Fit (92) | Psico: 95 | Test: 90",
            "5 years sourcing bilingual underwriting and accounting specialists across Sinaloa and Sonora. Strong recruiter network.",
            json.dumps({
                "candidate": "Valeria Beltrán",
                "applied_role": "Senior Talent Acquisition Specialist",
                "application_area": "Operations & Accounting",
                "candidate_fit_tier": "High Fit",
                "candidate_fit_score": 92,
                "psychometrics_score": 95,
                "knowledge_test_score": 90,
                "overall_fit_score": 92,
                "experience_years": 5,
                "cefr": "C1",
                "action": "Advance to Interview"
            }),
            "Pending Triage",
            0,
            "Google Meet via Fireflies.ai",
            ""
        ),

        # -------------------------------------------------------------
        # PROCESSED OPERATIONS (SYNCED TO SYSTEM - LIFO Recency)
        # -------------------------------------------------------------
        (
            t_minus_hours(2),
            "Robert Martinez",
            "Senior Underwriter",
            "credit",
            "Lone Star Cold Storage (Houston, TX)",
            "Low Risk | $150k USD",
            "Refrigerated warehousing expansion with $95k monthly revenues and 0.22 DTI ratio. Clean UCC lien history verified.",
            json.dumps({"risk_tier": "Low Risk", "requested_amount": 150000, "dti": 0.22, "collateral": "Warehouse Equipment"}),
            "Synced",
            1,
            "Google Meet / Read AI",
            "Verified 3 years tax returns and bank statements; 0.22 DTI confirmed."
        ),
        (
            t_minus_hours(3),
            "Sarah Jenkins",
            "Commercial BDR",
            "sales",
            "Desert Express Freight (El Paso, TX)",
            "Score: 88/100 | $1.8M ARR",
            "Regional dry-van carrier qualified for non-recourse factoring line. Cold email draft staged in Gmail for morning send.",
            json.dumps({"lead_score": 88, "arr": 1800000, "fleet_size": 12}),
            "Synced",
            1,
            "Google Meet / Fireflies.ai",
            "Qualified for 90-day non-recourse line; tailored cold email staged."
        ),
        (
            t_minus_hours(4),
            "Elena Ramos",
            "Talent Specialist",
            "hr",
            "Mateo Guerrero (Mazatlán, Sin.)",
            "High Fit (88) | Psico: 85 | Test: 87",
            "Solid cold calling experience in logistics staffing; fluent commercial English with fast speed-to-lead execution.",
            json.dumps({
                "candidate": "Mateo Guerrero",
                "applied_role": "Commercial BDR",
                "application_area": "Commercial Sales & BDR",
                "candidate_fit_tier": "High Fit",
                "candidate_fit_score": 88,
                "psychometrics_score": 85,
                "knowledge_test_score": 87,
                "overall_fit_score": 88,
                "cefr": "B2",
                "action": "Advance to Technical Interview"
            }),
            "Synced",
            1,
            "Google Meet / Read AI",
            "Demonstrated strong commercial objection handling; advanced to HM case study."
        ),
        (
            t_minus_hours(7),
            "Robert Martinez",
            "Senior Underwriter",
            "credit",
            "Pacific Shore Drywall (San Diego, CA)",
            "Low Risk | $110k USD",
            "Commercial subcontractor with verified general contractor pay applications. Rapid liquidity fit for weekly payroll.",
            json.dumps({"risk_tier": "Low Risk", "requested_amount": 110000, "dti": 0.25, "collateral": "GC Pay Applications"}),
            "Synced",
            1,
            "Google Meet / Read AI",
            "General contractor pay applications confirmed; no outstanding federal liens."
        ),
        (
            t_minus_days(1),
            "Sarah Jenkins",
            "Commercial BDR",
            "sales",
            "Sonora Freightlines (Nogales, AZ)",
            "Score: 92/100 | $3.1M ARR",
            "High-volume produce hauler facing 60-day broker lag. High-conversion telephone pitch delivered to dispatch director.",
            json.dumps({"lead_score": 92, "arr": 3100000, "fleet_size": 22}),
            "Synced",
            1,
            "Google Meet / Read AI",
            "High urgency produce liquidity fit; 350k factoring line approved."
        ),
        (
            t_minus_days(1),
            "Elena Ramos",
            "Talent Specialist",
            "hr",
            "Mariana Ochoa (Culiacán, Sin.)",
            "High Fit (91) | Psico: 94 | Test: 93",
            "Over 6 years financial analysis and underwriting leadership; exceptional cross-border commercial lending communication.",
            json.dumps({
                "candidate": "Mariana Ochoa",
                "applied_role": "Senior Underwriting Lead",
                "application_area": "Credit Underwriting & Risk",
                "candidate_fit_tier": "High Fit",
                "candidate_fit_score": 91,
                "psychometrics_score": 94,
                "knowledge_test_score": 93,
                "overall_fit_score": 91,
                "cefr": "C2",
                "action": "Direct Offer Recommended"
            }),
            "Synced",
            1,
            "Google Meet / Read AI",
            "Exceptional cross-border credit experience; recommend direct partner offer."
        ),
        (
            t_minus_days(2),
            "Robert Martinez",
            "Senior Underwriter",
            "credit",
            "Highland Precision Machining (Fort Worth, TX)",
            "Moderate Risk | $95k USD",
            "Aerospace tooling machine shop with verified purchase orders from Lockheed tier-2 supplier. Debt coverage DSCR at 1.34.",
            json.dumps({"risk_tier": "Moderate Risk", "requested_amount": 95000, "dscr": 1.34, "collateral": "Tooling Equipment"}),
            "Synced",
            1,
            "Google Meet / Read AI",
            "Lockheed tier-2 purchase orders verified; 1.34 DSCR meets criteria."
        ),
        (
            t_minus_days(3),
            "Sarah Jenkins",
            "Commercial BDR",
            "sales",
            "Cactus State Express (Tucson, AZ)",
            "Score: 78/100 | $1.2M ARR",
            "Dry bulk carrier with steady regional routes. Standard 3% factoring rate approved by commercial sales director.",
            json.dumps({"lead_score": 78, "arr": 1200000, "fleet_size": 7}),
            "Synced",
            1,
            "Google Meet / Fireflies.ai",
            "Standard 3% factoring rate approved; contracts staged."
        ),
        (
            t_minus_days(4),
            "Elena Ramos",
            "Talent Specialist",
            "hr",
            "Diego Carvajal (Mazatlán, Sin.)",
            "Moderate Fit (86) | Psico: 84 | Test: 82",
            "3 years banking documentation review in Mazatlán. Good understanding of balance sheet ratios and asset collateral.",
            json.dumps({
                "candidate": "Diego Carvajal",
                "applied_role": "Junior Credit Analyst",
                "application_area": "Credit Underwriting & Risk",
                "candidate_fit_tier": "Moderate Fit",
                "candidate_fit_score": 86,
                "psychometrics_score": 84,
                "knowledge_test_score": 82,
                "overall_fit_score": 86,
                "cefr": "B2",
                "action": "Advance to Case Study"
            }),
            "Synced",
            1,
            "Google Meet / Read AI",
            "Strong documentation instincts; case study assigned for Thursday."
        )
    ]

    cursor = conn.cursor()
    cursor.executemany("""
        INSERT INTO operations_history (
            timestamp, operator_name, operator_role, module_type,
            entity_name, headline_metric, assessment_summary,
            full_output_json, dispatch_status, is_processed, source_channel, analyst_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, organic_records)
    conn.commit()


def ingest_pending_record(
    module_type: str,
    entity_name: str,
    headline_metric: str,
    transcript_text: str,
    assessment_summary: str = "Awaiting discovery analysis",
    source_channel: str = "Google Meet via Read AI",
    doc_url: str = "",
    doc_note: str = "",
    metadata_extra: Optional[Dict[str, Any]] = None
) -> int:
    """
    Ingest a new pending record from an external source (n8n, Google Drive, Meeting Webhook).
    Places the item in the pending queue (is_processed=0) with current timestamp to start SLA tracking.
    """
    payload = {
        "transcript": transcript_text,
        "default_doc_url": doc_url,
        "doc_note": doc_note,
        "status": "pending_triage",
        "ingestion_source": source_channel
    }
    if metadata_extra and isinstance(metadata_extra, dict):
        payload.update(metadata_extra)

    return save_operation(
        operator_name="Unassigned (Intake Queue)",
        operator_role="Incoming Stream",
        module_type=module_type.lower(),
        entity_name=entity_name,
        headline_metric=headline_metric,
        assessment_summary=assessment_summary,
        full_output_json=payload,
        dispatch_status="Pending Triage",
        is_processed=0,
        source_channel=source_channel,
        analyst_notes=""
    )


def get_candidate_area(record: Dict[str, Any]) -> str:
    """
    Extract or intelligently infer the functional application area for an HR candidate record.
    Returns one of:
      - 'Credit Underwriting & Risk'
      - 'Commercial Sales & BDR'
      - 'Operations & Accounting'
      - 'Technology & Systems'
    """
    try:
        raw = record.get("full_output_json", "{}")
        d = json.loads(raw) if isinstance(raw, str) else (raw or {})
        if isinstance(d, dict) and d.get("application_area"):
            return d["application_area"]
    except Exception:
        pass

    text = (
        str(record.get("headline_metric", "")) + " " +
        str(record.get("entity_name", "")) + " " +
        str(record.get("assessment_summary", ""))
    ).lower()

    if any(k in text for k in ["credit", "underwriter", "underwriting", "risk", "analyst", "mca"]):
        return "Credit Underwriting & Risk"
    elif any(k in text for k in ["bdr", "sales", "outreach", "commercial", "calling"]):
        return "Commercial Sales & BDR"
    elif any(k in text for k in ["operations", "accounting", "recruiter", "talent", "hr", "sourcing"]):
        return "Operations & Accounting"
    elif any(k in text for k in ["technology", "systems", "it", "dev", "engineer", "software"]):
        return "Technology & Systems"
    return "Credit Underwriting & Risk"


def get_database_schema(table_name: str = "operations_history") -> List[Dict[str, Any]]:
    """Return table column metadata for database inspection."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    rows = cursor.fetchall()
    return [
        {
            "cid": r["cid"],
            "name": r["name"],
            "type": r["type"],
            "notnull": bool(r["notnull"]),
            "dflt_value": r["dflt_value"],
            "pk": bool(r["pk"])
        }
        for r in rows
    ]


def get_database_stats() -> Dict[str, Any]:
    """Retrieve database metrics including record counts and disk footprint."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM operations_history")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT module_type, COUNT(*) AS cnt FROM operations_history GROUP BY module_type")
    by_mod = {row["module_type"]: row["cnt"] for row in cursor.fetchall()}

    cursor.execute("SELECT is_processed, COUNT(*) AS cnt FROM operations_history GROUP BY is_processed")
    by_proc = {row["is_processed"]: row["cnt"] for row in cursor.fetchall()}

    file_size_bytes = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0

    return {
        "db_path": DB_PATH,
        "file_size_bytes": file_size_bytes,
        "file_size_kb": round(file_size_bytes / 1024, 2),
        "total_records": total,
        "credit_count": by_mod.get("credit", 0),
        "sales_count": by_mod.get("sales", 0),
        "hr_count": by_mod.get("hr", 0),
        "processed_count": by_proc.get(1, 0),
        "pending_count": by_proc.get(0, 0),
    }


def execute_safe_query(sql_query: str, max_rows: int = 100) -> Tuple[List[str], List[Tuple], Optional[str]]:
    """
    Safely execute read-only queries (SELECT, PRAGMA, EXPLAIN) in the SQLite database.
    Rejects mutation statements (DROP, DELETE, UPDATE, INSERT, ALTER) to protect production data.
    """
    cleaned = sql_query.strip()
    first_token = cleaned.split()[0].upper() if cleaned else ""
    if first_token not in ["SELECT", "PRAGMA", "EXPLAIN"]:
        return [], [], f"Security Policy Violation: Only read-only queries (SELECT, PRAGMA) are permitted. Received: '{first_token}'"

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(cleaned)
        col_names = [d[0] for d in cursor.description] if cursor.description else []
        rows = cursor.fetchmany(max_rows)
        return col_names, [tuple(r) for r in rows], None
    except Exception as exc:
        return [], [], str(exc)


def vacuum_database() -> Dict[str, Any]:
    """Execute VACUUM to reclaim unused disk space and optimize page allocation."""
    size_before = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    conn = get_connection()
    conn.execute("VACUUM")
    conn.execute("PRAGMA optimize")
    size_after = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    return {
        "size_before_bytes": size_before,
        "size_after_bytes": size_after,
        "reclaimed_bytes": max(0, size_before - size_after)
    }


