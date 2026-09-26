"""
SQLite Persistence Layer for DeskMate Operations Studio
Provides persistent audit trails, operational history, and cross-team review records.
"""
import os
import sqlite3
import json
import time
from typing import List, Dict, Any, Optional

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
            dispatch_status TEXT NOT NULL
        )
    """)
    conn.commit()

    # Check if empty, and seed sample historical activity if needed
    cursor.execute("SELECT COUNT(*) as count FROM operations_history")
    row = cursor.fetchone()
    if row["count"] == 0:
        seed_default_history(conn)
    conn.close()


def save_operation(
    operator_name: str,
    operator_role: str,
    module_type: str,
    entity_name: str,
    headline_metric: str,
    assessment_summary: str,
    full_output_json: Dict[str, Any],
    dispatch_status: str = "Synced with n8n / Sheets"
) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    cursor.execute("""
        INSERT INTO operations_history (
            timestamp, operator_name, operator_role, module_type,
            entity_name, headline_metric, assessment_summary,
            full_output_json, dispatch_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        operator_name,
        operator_role,
        module_type,
        entity_name,
        headline_metric,
        assessment_summary,
        json.dumps(full_output_json, ensure_ascii=False),
        dispatch_status
    ))
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id


def get_operations(limit: int = 50, module_type: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if module_type:
        cursor.execute(
            "SELECT * FROM operations_history WHERE module_type = ? ORDER BY id DESC LIMIT ?",
            (module_type, limit)
        )
    else:
        cursor.execute(
            "SELECT * FROM operations_history ORDER BY id DESC LIMIT ?",
            (limit,)
        )
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results


def seed_default_history(conn: sqlite3.Connection) -> None:
    sample_records = [
        (
            "2026-09-26 14:15:20",
            "Robert Martinez",
            "Senior Underwriter",
            "credit",
            "Apex Fleet Repair (Dallas, TX)",
            "Moderate Risk | $85k Requested",
            "Collateral confirmed with hydraulic lifts; active IRS lien has verified installment agreement in good standing.",
            json.dumps({"risk_tier": "Moderate Risk", "dti_ratio": "38%"}),
            "Synced to n8n / Underwriting Pipeline"
        ),
        (
            "2026-09-26 13:40:11",
            "Sarah Jenkins",
            "Commercial BDR",
            "sales",
            "Sunbelt Logistics LLC (Phoenix, AZ)",
            "Score: 88/100 | High Fit",
            "14-tractor refrigerated fleet with strong $2.4M ARR; ideal candidate for rapid invoice factoring facility.",
            json.dumps({"lead_score": 88, "recommended_service": "Invoice Factoring"}),
            "Synced to n8n / Sales CRM"
        ),
        (
            "2026-09-26 11:22:05",
            "Elena Ramos",
            "Talent Specialist",
            "hr",
            "Sofia Valdez (Mazatlán, Sin.)",
            "Fit Score: 94/100 | C1 Bilingual",
            "5 years underwriting experience at regional fintech; demonstrated exceptional credit memo structuring speed.",
            json.dumps({"fit_score": 94, "recommended_action": "Advance to Hiring Manager"}),
            "Synced to Greenhouse / HR Tracker"
        ),
    ]
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT INTO operations_history (
            timestamp, operator_name, operator_role, module_type,
            entity_name, headline_metric, assessment_summary,
            full_output_json, dispatch_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_records)
    conn.commit()
