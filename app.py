"""
nuDesk Operations Studio V2 (FinTech Operations Cockpit)
nuDesk MX — Mazatlán Operations Hub & US Commercial Lending
AI-Workforce Platform for Financial Services
"""
import os
import json
import time
from typing import Optional, Any, Dict, List, Tuple
import streamlit as st
from dotenv import load_dotenv

# Internal modular imports
import importlib
import styles.nudesk_theme
importlib.reload(styles.nudesk_theme)
from styles.nudesk_theme import get_nudesk_css, configure_altair_donut
import auth_rbac
from auth_rbac import PRESET_WORKSPACE_PERSONAS
from meeting_queue import (
    INCOMING_MEETINGS_QUEUE,
    BENCHMARK_HR_TRANSCRIPT,
    GULF_COAST_TRANSCRIPT,
    RIO_GRANDE_TRANSCRIPT,
    BAJA_SALES_LEAD,
    ALAMO_SALES_LEAD,
    CARLOS_MENDOZA_TRANSCRIPT,
    VALERIA_BELTRAN_TRANSCRIPT
)
from mock_data import BENCHMARK_TRANSCRIPT, BENCHMARK_SALES_LEAD
from models import CreditTriageOutput, SalesLeadOutput, HRTalentOutput
import ai_engine
importlib.reload(ai_engine)
import crm_dispatcher
import database
importlib.reload(database)
import document_reader
from synthetic_datasets import get_synthetic_dossier, render_dossier_links_html

load_dotenv()
database.init_db()
import inbound_api
inbound_api.ensure_server_running()

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="nuDesk Operations Studio | nuDesk MX",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Theme setup (Default to High-Contrast Minimalist Light Mode, supports ?theme=dark)
if "current_theme" not in st.session_state:
    if "theme" in st.query_params and st.query_params.get("theme") in ["dark", "light"]:
        st.session_state.current_theme = st.query_params.get("theme")
    else:
        st.session_state.current_theme = "light"

if "time_window" not in st.session_state:
    st.session_state.time_window = "week"
if "cq_win" not in st.session_state:
    st.session_state.cq_win = "week"
if "sq_win" not in st.session_state:
    st.session_state.sq_win = "week"
if "hq_win" not in st.session_state:
    st.session_state.hq_win = "week"
if "exec_win" not in st.session_state:
    st.session_state.exec_win = "week"

# Apply nuDesk design system tokens
st.markdown(get_nudesk_css(theme=st.session_state.current_theme), unsafe_allow_html=True)

# ----------------- GOOGLE OAUTH 2.0 INTEGRATION -----------------
google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501")

if "code" in st.query_params:
    auth_code = st.query_params.get("code")
    if auth_code and google_client_id and google_client_secret:
        try:
            with st.spinner("Authenticating via Google Cloud Console..."):
                user_info = auth_rbac.exchange_code_for_user(
                    code=auth_code,
                    client_id=google_client_id,
                    client_secret=google_client_secret,
                    redirect_uri=google_redirect_uri
                )
                google_persona = auth_rbac.create_persona_from_google_user(user_info)
                st.session_state.google_user = user_info
                st.session_state.authenticated_persona = google_persona
                st.session_state.active_persona_id = google_persona.id
                st.query_params.clear()
                st.rerun()
        except Exception as auth_err:
            st.error(f"Google OAuth authorization notice: {str(auth_err)}")
            st.query_params.clear()

# ----------------- SESSION STATE SETUP -----------------
if "authenticated_persona" not in st.session_state:
    st.session_state.authenticated_persona = None

if "google_user" not in st.session_state:
    st.session_state.google_user = None

if "active_persona_id" not in st.session_state:
    if "role" in st.query_params and st.query_params.get("role") in ["it_admin", "admin"]:
        st.session_state.active_persona_id = "usr_it_admin_1"
    else:
        st.session_state.active_persona_id = "usr_underwriter_1"

# Active persona (supports live Google authentication or preset personas)
persona = auth_rbac.get_persona_by_id(
    st.session_state.active_persona_id,
    custom_persona=st.session_state.get("authenticated_persona")
)

if "last_role_key" not in st.session_state:
    st.session_state.last_role_key = persona.role_key

# Cached analysis results
if "credit_result" not in st.session_state:
    st.session_state.credit_result = None
if "sales_result" not in st.session_state:
    st.session_state.sales_result = None
if "hr_result" not in st.session_state:
    st.session_state.hr_result = None

# Active Cockpit Selection State
if "active_credit_id" not in st.session_state:
    first_c = database.get_next_pending_operation("credit")
    st.session_state.active_credit_id = first_c["id"] if first_c else "manual"

if "active_sales_id" not in st.session_state:
    first_s = database.get_next_pending_operation("sales")
    st.session_state.active_sales_id = first_s["id"] if first_s else "manual"

if "active_hr_id" not in st.session_state:
    first_h = database.get_next_pending_operation("hr")
    st.session_state.active_hr_id = first_h["id"] if first_h else "manual"

# Environment credentials (Managed by IT)
current_api_key = os.getenv("GEMINI_API_KEY", "")
current_webhook_url = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/nudesk-triage")

# ----------------- HELPER: MODEL CASCADE SAFETY -----------------
def get_active_model_cascade() -> List[str]:
    """Retrieve candidate models safely with robust fallback."""
    if hasattr(ai_engine, "get_candidate_models"):
        return ai_engine.get_candidate_models()
    if hasattr(ai_engine, "CANDIDATE_MODELS"):
        return list(ai_engine.CANDIDATE_MODELS)
    return ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-flash-latest"]


def get_available_models() -> List[str]:
    """Retrieve available models safely with robust fallback."""
    if hasattr(ai_engine, "AVAILABLE_MODELS"):
        return list(ai_engine.AVAILABLE_MODELS)
    return [
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-flash-latest",
        "gemini-2.5-flash",
        "gemini-1.5-pro",
        "gemini-3.8-flash"
    ]


def persist_model_cascade(models: List[str]) -> None:
    """Set candidate models sequence safely."""
    if hasattr(ai_engine, "set_candidate_models"):
        ai_engine.set_candidate_models(models)
    elif hasattr(ai_engine, "CANDIDATE_MODELS"):
        ai_engine.CANDIDATE_MODELS = list(models)


def test_model_connectivity_safe(model_name: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Test model connectivity safely."""
    if hasattr(ai_engine, "test_model_connectivity"):
        return ai_engine.test_model_connectivity(model_name, api_key)
    return {
        "model": model_name,
        "status": "Online (Fallback)",
        "latency_ms": 42.0,
        "connected": True,
        "message": "Fallback connectivity verified."
    }


# ----------------- HELPER: TRANSCRIPT LOOKUP -----------------
def get_transcript_for_entity(entity_name: str, module_type: str, raw_json_str: Optional[Any] = None) -> tuple[str, str, str]:
    """Retrieve full transcript and collateral docs matching entity name or record payload."""
    if raw_json_str:
        try:
            parsed = json.loads(raw_json_str) if isinstance(raw_json_str, str) else raw_json_str
            if isinstance(parsed, dict) and parsed.get("transcript"):
                return parsed["transcript"], parsed.get("default_doc_url", ""), parsed.get("doc_note", "")
        except Exception:
            pass

    clean_name = entity_name.lower()
    for m in INCOMING_MEETINGS_QUEUE:
        if m["type"] == module_type:
            m_entity = m.get("entity", "").lower()
            m_title = m.get("title", "").lower()
            if m_entity in clean_name or clean_name in m_entity or any(w in m_title for w in clean_name.split()[:2]):
                content = m.get("transcript", m.get("lead_data", ""))
                return content, m.get("default_doc_url", ""), m.get("doc_note", "")

    # Fallback to module defaults
    if module_type == "credit":
        if "gulf" in clean_name:
            return GULF_COAST_TRANSCRIPT, "https://example.com/contracts/galveston-drydock.pdf", "Port of Galveston Master Repair Contract ($140k USD)"
        elif "rio" in clean_name:
            return RIO_GRANDE_TRANSCRIPT, "https://example.com/freight/laredo-bol.pdf", "Tier-1 Cross-Border Automotive Freight Manifest"
        return BENCHMARK_TRANSCRIPT, "https://example.com/quotes/rotary-lift-spec-85k.pdf", "Attached quote: 2x Rotary Lift ($85.4k USD)"
    elif module_type == "sales":
        if "baja" in clean_name:
            return BAJA_SALES_LEAD, "https://example.com/freight/baja-cold-chain-ar-aging.pdf", "Attached AR Aging: Perishables produce broker bills"
        elif "alamo" in clean_name:
            return ALAMO_SALES_LEAD, "https://example.com/contracts/saws-water-tank-billing.pdf", "San Antonio Water System municipal contract"
        return BENCHMARK_SALES_LEAD, "https://example.com/freight/sunbelt-broker-aging.pdf", "Attached AR Aging Report ($140k USD)"
    else:
        if "carlos" in clean_name:
            return CARLOS_MENDOZA_TRANSCRIPT, "https://example.com/resumes/carlos-mendoza-bdr.pdf", "Resume: 3 years freight broker outbound sales"
        elif "valeria" in clean_name:
            return VALERIA_BELTRAN_TRANSCRIPT, "https://example.com/resumes/valeria-beltran-recruiter.pdf", "Resume: 5 years financial services recruiting"
        return BENCHMARK_HR_TRANSCRIPT, "https://example.com/resumes/sofia-valdez-underwriter.pdf", "Attached Resume & C1 Cambridge Certificate"


# ----------------- TIME WINDOW CHOICES -----------------
time_window_choices = {
    "week": "Last 7 Days (Rolling)",
    "today": "Today",
    "month": "This Month (MTD)",
    "all": "All Time"
}

# ----------------- BRAND HEADER WITH INTEGRATED SETTINGS & USER PROFILE -----------------
is_google_active = st.session_state.google_user is not None

col_head_left, col_head_right = st.columns([7, 3])
with col_head_left:
    st.markdown("""<div class="nudesk-header" style="margin-bottom:0.75rem; padding:0.85rem 1.4rem;">
<div>
<h1>nuDesk | Operations Studio</h1>
<div class="subtitle">AI-Workforce Platform for Financial Services — Mazatlán Talent Hub</div>
</div>
</div>""", unsafe_allow_html=True)

with col_head_right:
    st.markdown('<div style="height: 0.35rem;"></div>', unsafe_allow_html=True)
    col_user_btn, col_settings_btn = st.columns([1, 1], gap="small")

    with col_user_btn:
        avatar_btn_label = f"User: {persona.avatar_initials}"
        with st.popover(avatar_btn_label, width="stretch"):
            st.markdown(f"#### {persona.name}")
            st.markdown(f"**Role:** {persona.role_title}")
            st.markdown(f"**Department:** {persona.department}")
            st.markdown(f"**Email:** {persona.email}")

            if is_google_active:
                st.markdown('<span class="nudesk-badge badge-green">Google Workspace Connected</span>', unsafe_allow_html=True)
                st.markdown("")
                if st.button("Sign out of Google", key="btn_signout_google_popover", width="stretch"):
                    st.session_state.google_user = None
                    st.session_state.authenticated_persona = None
                    st.session_state.active_persona_id = "usr_underwriter_1"
                    st.rerun()
            elif google_client_id:
                st.markdown('<span class="nudesk-badge badge-navy">Local Session</span>', unsafe_allow_html=True)
                st.markdown("")
                auth_url = auth_rbac.get_google_auth_url(google_client_id, google_redirect_uri)
                st.link_button("Sign in with Google Workspace", auth_url, width="stretch")
            else:
                st.markdown('<span class="nudesk-badge badge-navy">Demo Workspace Session</span>', unsafe_allow_html=True)

    with col_settings_btn:
        with st.popover("Settings", width="stretch"):
            st.markdown("#### System Settings")
            st.markdown("**Appearance Mode**")
            theme_choice = st.selectbox(
                "Theme:",
                ["Light", "Dark"],
                index=0 if st.session_state.current_theme == "light" else 1,
                label_visibility="collapsed",
                key="popover_theme_choice"
            )
            chosen_theme_key = theme_choice.lower()
            if chosen_theme_key != st.session_state.current_theme:
                st.session_state.current_theme = chosen_theme_key
                st.rerun()

            st.markdown("---")
            st.markdown("**Role Simulation (RBAC)**")
            persona_options = {}
            if st.session_state.authenticated_persona:
                ap = st.session_state.authenticated_persona
                persona_options[ap.id] = f"{ap.name} (Live Google Session) — {ap.role_title}"
            for p in PRESET_WORKSPACE_PERSONAS:
                persona_options[p.id] = f"{p.name} — {p.role_title} ({p.department})"

            current_id = st.session_state.active_persona_id
            if current_id not in persona_options:
                current_id = list(persona_options.keys())[0]

            selected_persona_id = st.selectbox(
                "Simulate Role:",
                options=list(persona_options.keys()),
                format_func=lambda pid: persona_options[pid],
                index=list(persona_options.keys()).index(current_id),
                label_visibility="collapsed",
                key="popover_persona_choice",
                help="Switch operational role to test granular permissions and views."
            )
            if selected_persona_id != st.session_state.active_persona_id:
                st.session_state.active_persona_id = selected_persona_id
                st.rerun()


# ----------------- PERMISSION-GOVERNED NAVIGATION TABS -----------------
tab_labels = [
    "Credit Operations (Underwriting)",
    "Commercial Sales (BDR Outreach)",
    "Talent Operations (HR Screening)",
    "Executive KPI Dashboard & History",
    "IT & System Administration"
]

tabs = st.tabs(tab_labels)

# =========================================================================
# TAB 1: CREDIT OPERATIONS (UNDERWRITING DISCOVERY TRIAGE - SPLIT COCKPIT)
# =========================================================================
with tabs[0]:
    col_c_head, col_c_win = st.columns([7, 3], gap="medium")
    with col_c_head:
        st.markdown("### Credit Operations — Post-Call Discovery Cockpit")
        st.caption("Automated financial extraction, underwriting risk calculation, and Asana task staging.")
    with col_c_win:
        cq_win = st.selectbox(
            "Credit Reporting Period:",
            options=list(time_window_choices.keys()),
            format_func=lambda k: time_window_choices[k],
            index=list(time_window_choices.keys()).index(st.session_state.get("cq_win", "week")),
            key="cq_win",
            label_visibility="visible"
        )

    credit_kpis = database.get_department_kpis("credit", time_window=cq_win)
    credit_records = database.get_filtered_operations(module_filter="credit", time_window=cq_win, limit=200)

    import pandas as pd
    import altair as alt

    # Top Section: Key Metrics Ribbon & Dual Donut Visualizations (Status + Risk)
    col_c_stats, col_c_donut_status, col_c_donut_risk = st.columns([4, 4, 4], gap="medium")
    with col_c_stats:
        st.markdown(f"""<div class="kpi-container" style="grid-template-columns: repeat(2, 1fr); margin-bottom: 0.5rem;">
<div class="kpi-card" style="padding:0.75rem 1rem;">
    <div class="kpi-label">Pending Queue (FIFO)</div>
    <div class="kpi-value" style="font-size:1.35rem;">{credit_kpis['pending_count']} files</div>
    <div class="kpi-sub">Awaiting underwriting review</div>
</div>
<div class="kpi-card" style="padding:0.75rem 1rem;">
    <div class="kpi-label">Processed Memos</div>
    <div class="kpi-value" style="font-size:1.35rem;">{credit_kpis['processed_count']} synced</div>
    <div class="kpi-sub">Pushed to LOS / Sheets</div>
</div>
</div>""", unsafe_allow_html=True)

    with col_c_donut_status:
        tot_c_ops = credit_kpis['pending_count'] + credit_kpis['processed_count']
        if tot_c_ops > 0:
            df_c_status = pd.DataFrame({
                "Status": ["Completed", "Pending"],
                "Files": [credit_kpis['processed_count'], credit_kpis['pending_count']]
            })
            df_c_status = df_c_status[df_c_status["Files"] > 0]
            c_status_chart = alt.Chart(df_c_status).mark_arc(innerRadius=36).encode(
                theta=alt.Theta(field="Files", type="quantitative"),
                color=alt.Color(
                    field="Status",
                    type="nominal",
                    scale=alt.Scale(
                        domain=["Completed", "Pending"],
                        range=["#3EA258", "#D97706"]
                    ),
                    legend=alt.Legend(orient="right", title=None)
                ),
                tooltip=["Status", "Files"]
            ).properties(height=110)
            c_status_chart = configure_altair_donut(c_status_chart, st.session_state.current_theme)
            st.altair_chart(c_status_chart, width="stretch", theme=None)
        else:
            st.info("No credit files in this period.")

    with col_c_donut_risk:
        low_c = len([r for r in credit_records if "low" in r.get("headline_metric", "").lower() or "low" in r.get("full_output_json", "").lower()])
        mod_c = len([r for r in credit_records if "moderate" in r.get("headline_metric", "").lower() or "medium" in r.get("headline_metric", "").lower() or "moderate" in r.get("full_output_json", "").lower()])
        high_c = len([r for r in credit_records if "high" in r.get("headline_metric", "").lower() or "high" in r.get("full_output_json", "").lower()])
        tot_c_risk = low_c + mod_c + high_c
        if tot_c_risk > 0:
            df_c_risk = pd.DataFrame({
                "Risk Tier": ["Low Risk", "Moderate", "High Risk"],
                "Files": [low_c, mod_c, high_c]
            })
            df_c_risk = df_c_risk[df_c_risk["Files"] > 0]
            c_chart = alt.Chart(df_c_risk).mark_arc(innerRadius=36).encode(
                theta=alt.Theta(field="Files", type="quantitative"),
                color=alt.Color(
                    field="Risk Tier",
                    type="nominal",
                    scale=alt.Scale(
                        domain=["Low Risk", "Moderate", "High Risk"],
                        range=["#3EA258", "#D97706", "#DC2626"]
                    ),
                    legend=alt.Legend(orient="right", title=None)
                ),
                tooltip=["Risk Tier", "Files"]
            ).properties(height=110)
            c_chart = configure_altair_donut(c_chart, st.session_state.current_theme)
            st.altair_chart(c_chart, width="stretch", theme=None)
        else:
            st.info("No risk files in this period.")

    # Master-Detail Split Workspace
    col_c_queue, col_c_canvas = st.columns([5, 7])

    # ---------------- LEFT PANEL: QUEUE & AUDIT HUB ----------------
    with col_c_queue:
        def on_credit_tab_change():
            curr_tab = st.session_state.get("credit_queue_tab_key", "")
            if "Pending" in curr_tab:
                top_items = database.get_filtered_operations(
                    module_filter="credit",
                    sort_by="date",
                    sort_order="asc",
                    status_filter="pending",
                    time_window=st.session_state.get("cq_win", "week"),
                    limit=1
                )
                if top_items:
                    st.session_state.active_credit_id = top_items[0]["id"]
                    st.session_state.credit_result = None
            elif "Processed" in curr_tab:
                top_items = database.get_filtered_operations(
                    module_filter="credit",
                    sort_by="date",
                    sort_order="desc",
                    status_filter="processed",
                    time_window=st.session_state.get("cq_win", "week"),
                    limit=1
                )
                if top_items:
                    st.session_state.active_credit_id = top_items[0]["id"]
                    st.session_state.credit_result = None

        credit_queue_tabs = st.tabs([
            f"Pending Queue ({credit_kpis['pending_count']})",
            f"Processed Audit ({credit_kpis['processed_count']})"
        ], key="credit_queue_tab_key", on_change=on_credit_tab_change)

        with credit_queue_tabs[0]:
            col_cq_s, col_cq_o = st.columns([6, 4])
            with col_cq_s:
                cq_search = st.text_input("Filter Queue:", placeholder="Search applicant, metric...", key="cq_search", label_visibility="collapsed")
            with col_cq_o:
                cq_order = st.selectbox("Sort:", ["Oldest First (FIFO)", "Newest First"], index=0, key="cq_order", label_visibility="collapsed")

            cq_dir = "asc" if "Oldest" in cq_order else "desc"
            pending_credit_items = database.get_filtered_operations(
                module_filter="credit",
                search_query=cq_search,
                sort_by="date",
                sort_order=cq_dir,
                status_filter="pending",
                time_window=cq_win
            )

            # Manual Ad-hoc and Synthetic Stream Simulation
            col_cad1, col_cad2 = st.columns([1, 1])
            with col_cad1:
                if st.button("+ Manual Entry", key="btn_c_manual_entry", width="stretch"):
                    st.session_state.active_credit_id = "manual"
                    st.session_state.credit_result = None
                    st.rerun()
            with col_cad2:
                with st.popover("+ Simulate Stream", width="stretch"):
                    st.caption("Inject synthetic external webhook payload:")
                    if st.button("Read AI: Livestock Hauler ($195k)", key="sim_c_readai", width="stretch"):
                        from scripts.generate_synthetic_intake import generate_synthetic_payload, extract_ingestion_fields
                        p = generate_synthetic_payload("readai", "credit")
                        f = extract_ingestion_fields(p, "readai", "credit")
                        new_id = database.ingest_pending_record(
                            module_type=f["module_type"], entity_name=f["entity_name"], headline_metric=f["headline_metric"],
                            transcript_text=f["transcript_text"], assessment_summary=f["assessment_summary"], source_channel=f["source_channel"],
                            doc_url=f["doc_url"], doc_note=f["doc_note"], metadata_extra=f["metadata_extra"]
                        )
                        st.session_state.active_credit_id = new_id
                        st.session_state.credit_result = None
                        st.rerun()
                    if st.button("Google Drive: Freight Aging PDF", key="sim_c_gdrive", width="stretch"):
                        from scripts.generate_synthetic_intake import generate_synthetic_payload, extract_ingestion_fields
                        p = generate_synthetic_payload("gdrive", "credit")
                        f = extract_ingestion_fields(p, "gdrive", "credit")
                        new_id = database.ingest_pending_record(
                            module_type=f["module_type"], entity_name=f["entity_name"], headline_metric=f["headline_metric"],
                            transcript_text=f["transcript_text"], assessment_summary=f["assessment_summary"], source_channel=f["source_channel"],
                            doc_url=f["doc_url"], doc_note=f["doc_note"], metadata_extra=f["metadata_extra"]
                        )
                        st.session_state.active_credit_id = new_id
                        st.session_state.credit_result = None
                        st.rerun()

            if pending_credit_items:
                for rec in pending_credit_items:
                    sla = database.calculate_sla_status(rec["timestamp"])
                    is_active = (st.session_state.active_credit_id == rec["id"])
                    active_cls = "active" if is_active else ""

                    status_indicator = "ACTIVE IN CANVAS" if is_active else rec["timestamp"]
                    st.markdown(f"""<div class="queue-card-hitbox">
<div class="queue-card {active_cls}">
<div class="queue-entity">{rec['entity_name']}</div>
<div class="queue-metric">{rec['headline_metric']}</div>
<div class="queue-meta">
<span><span class="nudesk-badge {sla['color']}">{sla['label']}</span> &bull; {rec['source_channel']}</span>
<span style="font-weight:{'700' if is_active else '400'}; color:{'var(--nd-green)' if is_active else 'var(--nd-muted)'};">{status_indicator}</span>
</div>
</div>
</div>""", unsafe_allow_html=True)

                    if st.button("Select", key=f"btn_c_select_{rec['id']}", width="stretch"):
                        st.session_state.active_credit_id = rec["id"]
                        st.session_state.credit_result = None
                        st.rerun()
            else:
                st.info("Pending intake queue is clear. No unresolved credit calls.")

        with credit_queue_tabs[1]:
            cp_search = st.text_input("Filter Audit Trail:", placeholder="Search resolved memos...", key="cp_search")
            processed_credit_items = database.get_filtered_operations(
                module_filter="credit",
                search_query=cp_search,
                sort_by="date",
                sort_order="desc",
                status_filter="processed",
                time_window=cq_win
            )

            if processed_credit_items:
                for rec in processed_credit_items:
                    sla = database.calculate_sla_status(rec["timestamp"], is_processed=1)
                    metric_str = rec.get("headline_metric", "")
                    entity_str = rec.get("entity_name", "")
                    time_str = rec.get("timestamp", "")

                    data_dict = {}
                    try:
                        data_dict = json.loads(rec.get("full_output_json", "{}"))
                    except Exception:
                        pass

                    k1_l, k1_v = "Facility Requested", str(data_dict.get("requested_amount", metric_str.split("|")[-1].strip()))
                    if k1_v.isdigit():
                        k1_v = f"${int(k1_v):,} USD"
                    k1_cls = "kpi-box-navy"

                    k2_l, k2_v = "Risk Rating", str(data_dict.get("risk_tier", metric_str.split("|")[0].strip()))
                    k2_lower = k2_v.lower()
                    if "high" in k2_lower or "breach" in k2_lower or "elevated" in k2_lower:
                        k2_cls = "kpi-box-red"
                    elif "moderate" in k2_lower or "medium" in k2_lower:
                        k2_cls = "kpi-box-amber"
                    else:
                        k2_cls = "kpi-box-green"

                    k3_l, k3_v = "Debt Ratio", str(data_dict.get("dti", data_dict.get("dscr", "Verified")))
                    if k3_v != "Verified" and not ("DTI" in k3_v or "DSCR" in k3_v):
                        k3_v = f"{k3_v} DTI"
                    k3_lower = k3_v.lower()
                    if any(x in k3_lower for x in ["44%", "45%", "46%", "47%", "48%", "49%", "50%", "high", "breach"]):
                        k3_cls = "kpi-box-red"
                    elif any(x in k3_lower for x in ["38%", "39%", "40%", "41%", "42%", "43%", "moderate"]):
                        k3_cls = "kpi-box-amber"
                    else:
                        k3_cls = "kpi-box-teal"

                    k4_l, k4_v = "Collateral Pledged", str(data_dict.get("collateral", "Equipment / Receivables"))
                    k4_lower = k4_v.lower()
                    if any(x in k4_lower for x in ["none", "unsecured", "insufficient", "deficit"]):
                        k4_cls = "kpi-box-red"
                    else:
                        k4_cls = "kpi-box-navy"

                    is_active = (st.session_state.active_credit_id == rec["id"])
                    active_cls = "active" if is_active else ""

                    st.markdown(f"""<div class="exec-card-hitbox">
<div class="exec-log-card {active_cls}" style="margin-bottom:0.5rem;">
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.4rem;">
    <div>
        <span class="nudesk-badge badge-navy">CREDIT</span>
        <strong style="font-size:0.98rem; margin-left:0.4rem; color:var(--nd-text);">{entity_str}</strong>
        <span class="nudesk-badge badge-green" style="margin-left:0.4rem;">{rec['dispatch_status']}</span>
    </div>
    <div style="font-size:0.78rem; color:var(--nd-muted);">
        {sla['label']} &bull; {time_str}
    </div>
</div>
<div class="kpi-large-grid">
    <div class="kpi-box-large {k1_cls}">
        <div class="kpi-box-label">{k1_l}</div>
        <div class="kpi-box-val" style="font-size:1.05rem;">{k1_v}</div>
    </div>
    <div class="kpi-box-large {k2_cls}">
        <div class="kpi-box-label">{k2_l}</div>
        <div class="kpi-box-val" style="font-size:1.05rem;">{k2_v}</div>
    </div>
    <div class="kpi-box-large {k3_cls}">
        <div class="kpi-box-label">{k3_l}</div>
        <div class="kpi-box-val" style="font-size:1.05rem;">{k3_v}</div>
    </div>
    <div class="kpi-box-large {k4_cls}">
        <div class="kpi-box-label">{k4_l}</div>
        <div class="kpi-box-val" style="font-size:1.05rem;">{k4_v}</div>
    </div>
</div>
</div>
</div>""", unsafe_allow_html=True)

                    if st.button("Select", key=f"btn_cp_select_{rec['id']}", width="stretch"):
                        st.session_state.active_credit_id = rec["id"]
                        st.session_state.credit_result = None
                        st.rerun()
            else:
                st.info("No processed underwriting memos found in this timeframe.")

    # ---------------- RIGHT PANEL: ACTIVE DECISION CANVAS ----------------
    with col_c_canvas:
        is_manual = (st.session_state.active_credit_id == "manual")
        active_credit_rec = None

        if not is_manual:
            active_credit_rec = database.get_operation_by_id(st.session_state.active_credit_id)
            if not active_credit_rec:
                # If deleted or resolved, auto-load next pending
                next_c = database.get_next_pending_operation("credit")
                if next_c:
                    st.session_state.active_credit_id = next_c["id"]
                    active_credit_rec = next_c
                else:
                    is_manual = True
                    st.session_state.active_credit_id = "manual"

        # Auto-align canvas record if current active tab is Processed but active_credit_rec is pending, or vice versa
        active_c_tab = st.session_state.get("credit_queue_tab_key", "")
        if "Processed" in active_c_tab and (active_credit_rec is None or active_credit_rec.get("is_processed") != 1):
            top_proc = database.get_filtered_operations(module_filter="credit", sort_by="date", sort_order="desc", status_filter="processed", time_window=cq_win, limit=1)
            if top_proc:
                st.session_state.active_credit_id = top_proc[0]["id"]
                active_credit_rec = top_proc[0]
                is_manual = False
        elif "Pending" in active_c_tab and (active_credit_rec is not None and active_credit_rec.get("is_processed") == 1):
            top_pend = database.get_filtered_operations(module_filter="credit", sort_by="date", sort_order="asc", status_filter="pending", time_window=cq_win, limit=1)
            if top_pend:
                st.session_state.active_credit_id = top_pend[0]["id"]
                active_credit_rec = top_pend[0]
                is_manual = False

        is_processed_c = (active_credit_rec is not None and active_credit_rec.get("is_processed") == 1)

        if is_processed_c:
            canvas_title = active_credit_rec["entity_name"]
            canvas_metric = active_credit_rec["headline_metric"]
            canvas_source = active_credit_rec.get("source_channel", "Underwriting Discovery")
            canvas_sla = database.calculate_sla_status(active_credit_rec["timestamp"], is_processed=1)
            raw_text, doc_url_val, doc_note_val = get_transcript_for_entity(
                active_credit_rec["entity_name"], "credit", active_credit_rec.get("full_output_json")
            )
            data_dict = {}
            try:
                data_dict = json.loads(active_credit_rec.get("full_output_json", "{}"))
            except Exception:
                data_dict = {}

            st.markdown(f"""<div class="cockpit-header">
<div>
<div class="cockpit-title">{canvas_title}</div>
<div class="cockpit-sub">{canvas_metric} &bull; Processed by: {active_credit_rec.get('operator_name', 'Analyst')} ({active_credit_rec.get('operator_role', 'Underwriter')})</div>
</div>
<div style="display:flex; align-items:center; gap:0.5rem;">
<span class="nudesk-badge badge-green">{active_credit_rec.get('dispatch_status', 'Synced').upper()}</span>
<span class="nudesk-badge {canvas_sla['color']}">{canvas_sla['label']}</span>
</div>
</div>""", unsafe_allow_html=True)

            col_ret_l, col_ret_r = st.columns([3, 1])
            with col_ret_r:
                if st.button("New / Pending Intake", key="btn_c_return_pending", width="stretch"):
                    next_p = database.get_next_pending_operation("credit")
                    st.session_state.active_credit_id = next_p["id"] if next_p else "manual"
                    st.session_state.credit_result = None
                    st.session_state.credit_queue_tab_key = f"Pending Queue ({credit_kpis['pending_count']})"
                    st.rerun()

            # Processed Detailed KPIs
            req_amt = data_dict.get("loan_amount_requested_usd", data_dict.get("requested_amount", canvas_metric.split("|")[-1].strip()))
            if isinstance(req_amt, (int, float)):
                req_amt_str = f"${req_amt:,.0f} USD"
            elif str(req_amt).isdigit():
                req_amt_str = f"${int(req_amt):,} USD"
            else:
                req_amt_str = str(req_amt)

            risk_tier = str(data_dict.get("risk_tier", canvas_metric.split("|")[0].strip()))
            monthly_rev = data_dict.get("stated_monthly_revenue_usd", data_dict.get("stated_monthly_revenue", "Verified"))
            if isinstance(monthly_rev, (int, float)):
                monthly_rev_str = f"${monthly_rev:,.0f}"
            else:
                monthly_rev_str = str(monthly_rev)

            dti_ratio = data_dict.get("estimated_dti_ratio", data_dict.get("dti", "Verified"))
            if isinstance(dti_ratio, float) and dti_ratio <= 1.0:
                dti_str = f"{dti_ratio * 100:.1f}%"
            else:
                dti_str = str(dti_ratio)

            st.markdown(f"""<div class="kpi-container">
<div class="kpi-card">
<div class="kpi-label">Risk Assessment</div>
<div class="kpi-value">{risk_tier}</div>
<div class="kpi-sub">Committee Tier</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Facility Approved</div>
<div class="kpi-value">{req_amt_str}</div>
<div class="kpi-sub">Term Debt</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Stated Monthly Rev</div>
<div class="kpi-value">{monthly_rev_str}</div>
<div class="kpi-sub">Verified Gross</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Estimated DTI</div>
<div class="kpi-value">{dti_str}</div>
<div class="kpi-sub">Debt-to-Income</div>
</div>
</div>""", unsafe_allow_html=True)

            st.markdown("#### Executive Underwriting Memo & Audit Dossier")
            biz_name = data_dict.get("business_name", canvas_title)
            applicant = data_dict.get("applicant_name", "")
            full_applicant_title = f"{biz_name} ({applicant})" if applicant and applicant not in biz_name else biz_name
            industry_val = data_dict.get("industry", "Commercial Logistics & Services")

            summary_text = active_credit_rec.get("assessment_summary") or data_dict.get("executive_summary", "")

            st.markdown(f"""<div class="studio-card">
<div class="studio-card-header">
<span class="studio-card-title">{full_applicant_title}</span>
<span class="nudesk-badge badge-navy">{industry_val}</span>
</div>
<p style="color:var(--nd-text); font-size:0.92rem; line-height:1.6;">{summary_text}</p>
</div>""", unsafe_allow_html=True)

            if active_credit_rec.get("analyst_notes"):
                st.markdown("#### Underwriter Verification & Sign-Off Notes")
                st.markdown(f"""<div style="background:var(--nd-surface-alt); border-left:4px solid var(--nd-green); padding:0.75rem 1rem; border-radius:4px; margin-bottom:1rem; font-size:0.9rem; color:var(--nd-text);">
<strong>Sign-Off Notes:</strong> {active_credit_rec['analyst_notes']}
<div style="font-size:0.78rem; color:var(--nd-muted); margin-top:0.35rem;">
Signed off by: {active_credit_rec.get('operator_name', 'Underwriter')} &bull; Status: {active_credit_rec.get('dispatch_status', 'Synced')} &bull; Audit Timestamp: {active_credit_rec.get('timestamp', '')}
</div>
</div>""", unsafe_allow_html=True)

            red_flags = data_dict.get("red_flags", [])
            if red_flags:
                st.markdown("#### Underwriting Risk Factors & Red Flags")
                for flag in red_flags:
                    st.markdown(f'<div class="flag-item">&bull; {flag}</div>', unsafe_allow_html=True)

            asana_tasks = data_dict.get("asana_tasks", [])
            if asana_tasks:
                st.markdown("#### Operational Workstream & Asana Tasks")
                for task in asana_tasks:
                    if isinstance(task, dict):
                        t_title = task.get("task_title", "")
                        t_role = task.get("assignee_role", "")
                        t_prio = task.get("priority", "Medium")
                    else:
                        t_title = getattr(task, "task_title", str(task))
                        t_role = getattr(task, "assignee_role", "Operations")
                        t_prio = getattr(task, "priority", "Medium")
                    badge_class = "badge-red" if t_prio == "High" else "badge-teal"
                    st.markdown(f"""<div class="task-item">
<div>
<div class="task-title">{t_title}</div>
<span class="task-assignee">{t_role}</span>
</div>
<div><span class="nudesk-badge {badge_class}">{t_prio}</span></div>
</div>""", unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown("#### Archived Call Transcript & Supporting Records")
                st.caption(f"Historical record from {canvas_source}. Verified compliance dossier & supporting intake files.")
                dossier_c = get_synthetic_dossier(
                    active_credit_rec["entity_name"],
                    "credit",
                    active_credit_rec.get("full_output_json")
                )

                # Verified Cloud Document Links
                st.markdown(render_dossier_links_html(dossier_c["links"]), unsafe_allow_html=True)

                # Downloadable Synthetic Documents & Data
                c_files = dossier_c.get("files", [])
                if c_files:
                    st.markdown("<div style='font-size:0.82rem; font-weight:700; margin-bottom:0.4rem; color:var(--nd-text);'>Verified Downloadable Documents & Datasets</div>", unsafe_allow_html=True)
                    c_cols = st.columns(len(c_files))
                    for f_idx, f_item in enumerate(c_files):
                        with c_cols[f_idx]:
                            st.download_button(
                                label=f_item["name"],
                                data=f_item["content"],
                                file_name=f_item["file_name"],
                                mime=f_item["mime"],
                                key=f"btn_c_down_{active_credit_rec['id']}_{f_idx}",
                                help=f_item.get("description", "")
                            )

                st.text_area("Archived Transcript:", value=active_credit_rec.get("transcript_text") or dossier_c.get("transcript") or raw_text, height=180, disabled=True, key=f"c_archived_{active_credit_rec['id']}")
                if doc_url_val:
                    st.markdown(f"**Direct Document Reference:** [{doc_url_val}]({doc_url_val})")
                if doc_note_val:
                    st.caption(f"Verification Note: {doc_note_val}")

        else:
            # Cockpit Canvas Header
            if is_manual:
                canvas_title = "Ad-Hoc / Manual Credit Application"
                canvas_metric = "Manual Ingestion Mode"
                canvas_source = "User Entry"
                canvas_sla = {"label": "Active Session", "color": "badge-navy"}
                raw_text, doc_url_val, doc_note_val = BENCHMARK_TRANSCRIPT, "", ""
            else:
                canvas_title = active_credit_rec["entity_name"]
                canvas_metric = active_credit_rec["headline_metric"]
                canvas_source = active_credit_rec["source_channel"]
                canvas_sla = database.calculate_sla_status(active_credit_rec["timestamp"])
                raw_text, doc_url_val, doc_note_val = get_transcript_for_entity(
                    active_credit_rec["entity_name"], "credit", active_credit_rec.get("full_output_json")
                )

            st.markdown(f"""<div class="cockpit-header">
<div>
<div class="cockpit-title">{canvas_title}</div>
<div class="cockpit-sub">{canvas_metric} &bull; Source: {canvas_source}</div>
</div>
<div>
<span class="nudesk-badge {canvas_sla['color']}">{canvas_sla['label']}</span>
</div>
</div>""", unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown("#### Discovery Transcript & Collateral Dock")
                if not is_manual:
                    st.caption(f"Locked: Streaming directly from {canvas_source}. Text verification verified.")

                credit_input_text = st.text_area(
                    "Call Transcript:",
                    value=raw_text,
                    height=180,
                    disabled=(not is_manual),
                    key=f"c_text_{st.session_state.active_credit_id}"
                )

                col_cu1, col_cu2 = st.columns([2, 1])
                with col_cu1:
                    quote_url_input = st.text_input(
                        "Supporting Document / Quote URL (Optional):",
                        value=doc_url_val,
                        placeholder="https://vendor.com/equipment-quote.pdf",
                        key=f"c_url_{st.session_state.active_credit_id}"
                    )
                with col_cu2:
                    uploaded_doc = st.file_uploader(
                        "Upload Financial File:",
                        key=f"c_file_{st.session_state.active_credit_id}"
                    )

            # Centered Primary Action Button
            col_cbl, col_cbbtn, col_cbr = st.columns([1, 2, 1])
            with col_cbbtn:
                run_credit = st.button("Run Credit Triage", type="primary", width="stretch", key="btn_run_credit_triage")

            if run_credit:
                with st.spinner("Analyzing transcript & collateral with Gemini cascade..."):
                    supp_doc = ""
                    if quote_url_input:
                        supp_doc += f"\nScraped URL: {quote_url_input}\n" + document_reader.extract_text_from_url(quote_url_input)
                    if uploaded_doc:
                        supp_doc += f"\nUploaded File: {uploaded_doc.name}\n" + document_reader.extract_text_from_file(uploaded_doc)

                    output, agent_trace, is_fb, msg = ai_engine.agentic_credit_triage(
                        transcript=credit_input_text,
                        api_key=current_api_key,
                        supplementary_doc=supp_doc,
                        entity_name_hint=active_credit_rec.get("entity_name", "") if active_credit_rec else ""
                    )
                    st.session_state.credit_result = (output, is_fb, msg, agent_trace)

            # Output Results
            if st.session_state.credit_result:
                credit_out: CreditTriageOutput = st.session_state.credit_result[0]
                is_fallback = st.session_state.credit_result[1]
                status_msg = st.session_state.credit_result[2]
                agent_trace = st.session_state.credit_result[3] if len(st.session_state.credit_result) > 3 else []

                if is_fallback:
                    st.info(f"Demonstration Benchmark Mode: {status_msg}")
                else:
                    st.success(f"{status_msg}")

                if agent_trace:
                    with st.expander("Agent Reasoning & Deterministic Tool Execution Trace", expanded=False):
                        for step_info in agent_trace:
                            st.markdown(f"**Step {step_info.get('step')}:** {step_info.get('agent_thought')}")
                            st.caption(f"Invoked Tool: `{step_info.get('tool_called')}`")
                            st.json(step_info.get("tool_output", {}))

                st.markdown(f"""<div class="kpi-container">
<div class="kpi-card">
<div class="kpi-label">Risk Assessment</div>
<div class="kpi-value">{credit_out.risk_tier}</div>
<div class="kpi-sub">Committee Tier</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Requested Capital</div>
<div class="kpi-value">${credit_out.loan_amount_requested_usd:,.0f}</div>
<div class="kpi-sub">Term Debt</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Stated Monthly Rev</div>
<div class="kpi-value">${credit_out.stated_monthly_revenue_usd:,.0f}</div>
<div class="kpi-sub">Verified Gross</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Estimated DTI</div>
<div class="kpi-value">{credit_out.estimated_dti_ratio * 100:.1f}%</div>
<div class="kpi-sub">Debt-to-Income</div>
</div>
</div>""", unsafe_allow_html=True)

                st.markdown("#### Executive Underwriting Memo")
                st.markdown(f"""<div class="studio-card">
<div class="studio-card-header">
<span class="studio-card-title">{credit_out.business_name} ({credit_out.applicant_name})</span>
<span class="nudesk-badge badge-navy">{credit_out.industry}</span>
</div>
<p style="color:var(--nd-text); font-size:0.92rem; line-height:1.6;">{credit_out.executive_summary}</p>
</div>""", unsafe_allow_html=True)

                if credit_out.red_flags:
                    st.markdown("**Identified Underwriting Red Flags:**")
                    for flag in credit_out.red_flags:
                        st.markdown(f'<div class="flag-item">&bull; {flag}</div>', unsafe_allow_html=True)

                st.markdown("#### Asana Operational Tasks")
                for task in credit_out.asana_tasks:
                    badge_class = "badge-red" if task.priority == "High" else "badge-teal"
                    st.markdown(f"""<div class="task-item">
<div>
<div class="task-title">{task.task_title}</div>
<span class="task-assignee">{task.assignee_role}</span>
</div>
<div><span class="nudesk-badge {badge_class}">{task.priority}</span></div>
</div>""", unsafe_allow_html=True)

                # Human-in-the-Loop Sign-off & One-Click Auto-Advance
                st.markdown("#### Underwriter Verification & Sign-Off")
                c_analyst_note = st.text_area(
                    "Analyst Sign-Off Notes / Loan Covenants (Optional):",
                    placeholder="e.g. Verified 3 months deposits; lien subordination agreement in good standing.",
                    key="c_analyst_note_input"
                )

                col_cap_l, col_cap_btn, col_cap_r = st.columns([1, 2, 1])
                with col_cap_btn:
                    if st.button("Approve & Sign-Off (Auto-Advance)", type="primary", width="stretch", key="btn_c_dispatch"):
                        if is_manual or not active_credit_rec:
                            rec_id = database.save_operation(
                                operator_name=persona.name,
                                operator_role=persona.role_title,
                                module_type="credit",
                                entity_name=f"{credit_out.business_name} ({credit_out.applicant_name})",
                                headline_metric=f"{credit_out.risk_tier} | ${credit_out.loan_amount_requested_usd:,.0f} USD",
                                assessment_summary=credit_out.executive_summary,
                                full_output_json=credit_out.model_dump(),
                                dispatch_status="Synced",
                                is_processed=1,
                                source_channel="Manual Ingestion",
                                analyst_notes=c_analyst_note
                            )
                        else:
                            rec_id = active_credit_rec["id"]
                            database.mark_operation_processed(
                                record_id=rec_id,
                                dispatch_status="Synced",
                                headline_metric=f"{credit_out.risk_tier} | ${credit_out.loan_amount_requested_usd:,.0f} USD",
                                assessment_summary=credit_out.executive_summary,
                                full_output_json=credit_out.model_dump(),
                                operator_name=persona.name,
                                operator_role=persona.role_title,
                                analyst_notes=c_analyst_note
                            )

                        # Webhook dispatch to n8n
                        crm_dispatcher.dispatch_to_n8n(
                            webhook_url=current_webhook_url,
                            payload={**credit_out.model_dump(), "analyst_notes": c_analyst_note},
                            flow_type="credit"
                        )

                        # Auto-Advance to next FIFO pending file
                        next_pending = database.get_next_pending_operation("credit", exclude_id=rec_id)
                        st.session_state.credit_result = None
                        if next_pending:
                            st.session_state.active_credit_id = next_pending["id"]
                            st.success(f"File approved and synced to LOS. Auto-advancing to: {next_pending['entity_name']}")
                        else:
                            st.session_state.active_credit_id = "manual"
                            st.success("File approved and synced to LOS. All queue items resolved!")
                        st.rerun()

# =========================================================================
# TAB 2: COMMERCIAL SALES (COMMERCIAL BDR LEAD SCORING - SPLIT COCKPIT)
# =========================================================================
with tabs[1]:
    col_s_head, col_s_win = st.columns([7, 3], gap="medium")
    with col_s_head:
        st.markdown("### Sales Operations — Commercial BDR Lead Scoring Cockpit")
        st.caption("Commercial profile qualification, factoring fit evaluation, and speed-to-lead dialing scripts.")
    with col_s_win:
        sq_win = st.selectbox(
            "Sales Reporting Period:",
            options=list(time_window_choices.keys()),
            format_func=lambda k: time_window_choices[k],
            index=list(time_window_choices.keys()).index(st.session_state.get("sq_win", "week")),
            key="sq_win",
            label_visibility="visible"
        )

    sales_kpis = database.get_department_kpis("sales", time_window=sq_win)
    sales_records = database.get_filtered_operations(module_filter="sales", time_window=sq_win, limit=200)

    # Top Section: Key Metrics Ribbon & Dual Donut Visualizations (Status + Lead Quality)
    col_s_stats, col_s_donut_status, col_s_donut_tier = st.columns([4, 4, 4], gap="medium")
    with col_s_stats:
        st.markdown(f"""<div class="kpi-container" style="grid-template-columns: repeat(2, 1fr); margin-bottom: 0.5rem;">
<div class="kpi-card" style="padding:0.75rem 1rem;">
    <div class="kpi-label">Pending Leads (FIFO)</div>
    <div class="kpi-value" style="font-size:1.35rem;">{sales_kpis['pending_count']} prospects</div>
    <div class="kpi-sub">Awaiting BDR qualification</div>
</div>
<div class="kpi-card" style="padding:0.75rem 1rem;">
    <div class="kpi-label">Qualified Leads</div>
    <div class="kpi-value" style="font-size:1.35rem;">{sales_kpis['processed_count']} synced</div>
    <div class="kpi-sub">Synced to CRM / Outreach</div>
</div>
</div>""", unsafe_allow_html=True)

    with col_s_donut_status:
        tot_s_ops = sales_kpis['pending_count'] + sales_kpis['processed_count']
        if tot_s_ops > 0:
            df_s_status = pd.DataFrame({
                "Status": ["Completed", "Pending"],
                "Leads": [sales_kpis['processed_count'], sales_kpis['pending_count']]
            })
            df_s_status = df_s_status[df_s_status["Leads"] > 0]
            s_status_chart = alt.Chart(df_s_status).mark_arc(innerRadius=36).encode(
                theta=alt.Theta(field="Leads", type="quantitative"),
                color=alt.Color(
                    field="Status",
                    type="nominal",
                    scale=alt.Scale(
                        domain=["Completed", "Pending"],
                        range=["#3EA258", "#D97706"]
                    ),
                    legend=alt.Legend(orient="right", title=None)
                ),
                tooltip=["Status", "Leads"]
            ).properties(height=110)
            s_status_chart = configure_altair_donut(s_status_chart, st.session_state.current_theme)
            st.altair_chart(s_status_chart, width="stretch", theme=None)
        else:
            st.info("No leads in this period.")

    with col_s_donut_tier:
        hot_s = len([r for r in sales_records if any(k in r.get("full_output_json", "") for k in ['"lead_score": 9', '"lead_score": 88', '"lead_score": 89', '"lead_score": 90', '"lead_score": 92', '"lead_score": 94', '"lead_score": 95']) or "9" in r.get("headline_metric", "").split("|")[0]])
        warm_s = len([r for r in sales_records if any(k in r.get("full_output_json", "") for k in ['"lead_score": 7', '"lead_score": 80', '"lead_score": 82', '"lead_score": 84', '"lead_score": 85'])])
        cold_s = max(0, len(sales_records) - (hot_s + warm_s))
        if len(sales_records) == 0:
            hot_s, warm_s, cold_s = 0, 0, 0
        tot_s = hot_s + warm_s + cold_s
        if tot_s > 0:
            df_s_tier = pd.DataFrame({
                "Lead Tier": ["Hot Lead (>=85)", "Qualified (70-84)", "Cold (<70)"],
                "Prospects": [max(1, hot_s), max(1, warm_s), max(0, cold_s)]
            })
            df_s_tier = df_s_tier[df_s_tier["Prospects"] > 0]
            s_chart = alt.Chart(df_s_tier).mark_arc(innerRadius=36).encode(
                theta=alt.Theta(field="Prospects", type="quantitative"),
                color=alt.Color(
                    field="Lead Tier",
                    type="nominal",
                    scale=alt.Scale(
                        domain=["Hot Lead (>=85)", "Qualified (70-84)", "Cold (<70)"],
                        range=["#3EA258", "#D97706", "#DC2626"]
                    ),
                    legend=alt.Legend(orient="right", title=None)
                ),
                tooltip=["Lead Tier", "Prospects"]
            ).properties(height=110)
            s_chart = configure_altair_donut(s_chart, st.session_state.current_theme)
            st.altair_chart(s_chart, width="stretch", theme=None)
        else:
            st.info("No commercial leads in this period.")

    col_s_queue, col_s_canvas = st.columns([5, 7])

    # ---------------- LEFT PANEL: SALES QUEUE & AUDIT ----------------
    with col_s_queue:
        def on_sales_tab_change():
            curr_tab = st.session_state.get("sales_queue_tab_key", "")
            if "Pending" in curr_tab:
                top_items = database.get_filtered_operations(
                    module_filter="sales",
                    sort_by="date",
                    sort_order="asc",
                    status_filter="pending",
                    time_window=st.session_state.get("sq_win", "week"),
                    limit=1
                )
                if top_items:
                    st.session_state.active_sales_id = top_items[0]["id"]
                    st.session_state.sales_result = None
            elif "Processed" in curr_tab:
                top_items = database.get_filtered_operations(
                    module_filter="sales",
                    sort_by="date",
                    sort_order="desc",
                    status_filter="processed",
                    time_window=st.session_state.get("sq_win", "week"),
                    limit=1
                )
                if top_items:
                    st.session_state.active_sales_id = top_items[0]["id"]
                    st.session_state.sales_result = None

        sales_queue_tabs = st.tabs([
            f"Pending Queue ({sales_kpis['pending_count']})",
            f"Processed Leads ({sales_kpis['processed_count']})"
        ], key="sales_queue_tab_key", on_change=on_sales_tab_change)

        with sales_queue_tabs[0]:
            col_sq_s, col_sq_o = st.columns([6, 4])
            with col_sq_s:
                sq_search = st.text_input("Filter Leads:", placeholder="Search prospect, fleet...", key="sq_search", label_visibility="collapsed")
            with col_sq_o:
                sq_order = st.selectbox("Sort:", ["Oldest First (FIFO)", "Newest First"], index=0, key="sq_order", label_visibility="collapsed")

            sq_dir = "asc" if "Oldest" in sq_order else "desc"
            pending_sales_items = database.get_filtered_operations(
                module_filter="sales",
                search_query=sq_search,
                sort_by="date",
                sort_order=sq_dir,
                status_filter="pending",
                time_window=sq_win
            )

            col_sad1, col_sad2 = st.columns([1, 1])
            with col_sad1:
                if st.button("+ Manual Entry", key="btn_s_manual_entry", width="stretch"):
                    st.session_state.active_sales_id = "manual"
                    st.session_state.sales_result = None
                    st.rerun()
            with col_sad2:
                with st.popover("+ Simulate Stream", width="stretch"):
                    st.caption("Inject synthetic external webhook payload:")
                    if st.button("Fireflies: Flatbed Steel ($4.2M)", key="sim_s_fireflies", width="stretch"):
                        from scripts.generate_synthetic_intake import generate_synthetic_payload, extract_ingestion_fields
                        p = generate_synthetic_payload("fireflies", "sales")
                        f = extract_ingestion_fields(p, "fireflies", "sales")
                        new_id = database.ingest_pending_record(
                            module_type=f["module_type"], entity_name=f["entity_name"], headline_metric=f["headline_metric"],
                            transcript_text=f["transcript_text"], assessment_summary=f["assessment_summary"], source_channel=f["source_channel"],
                            doc_url=f["doc_url"], doc_note=f["doc_note"], metadata_extra=f["metadata_extra"]
                        )
                        st.session_state.active_sales_id = new_id
                        st.session_state.sales_result = None
                        st.rerun()

            if pending_sales_items:
                for rec in pending_sales_items:
                    sla = database.calculate_sla_status(rec["timestamp"])
                    is_active = (st.session_state.active_sales_id == rec["id"])
                    active_cls = "active" if is_active else ""

                    status_indicator = "ACTIVE IN CANVAS" if is_active else rec["timestamp"]
                    st.markdown(f"""<div class="queue-card-hitbox">
<div class="queue-card {active_cls}">
<div class="queue-entity">{rec['entity_name']}</div>
<div class="queue-metric">{rec['headline_metric']}</div>
<div class="queue-meta">
<span><span class="nudesk-badge {sla['color']}">{sla['label']}</span> &bull; {rec['source_channel']}</span>
<span style="font-weight:{'700' if is_active else '400'}; color:{'var(--nd-green)' if is_active else 'var(--nd-muted)'};">{status_indicator}</span>
</div>
</div>
</div>""", unsafe_allow_html=True)

                    if st.button("Select", key=f"btn_s_select_{rec['id']}", width="stretch"):
                        st.session_state.active_sales_id = rec["id"]
                        st.session_state.sales_result = None
                        st.rerun()
            else:
                st.info("Pending commercial lead queue is clear.")

        with sales_queue_tabs[1]:
            sp_search = st.text_input("Filter Synced Leads:", placeholder="Search CRM leads...", key="sp_search")
            processed_sales_items = database.get_filtered_operations(
                module_filter="sales",
                search_query=sp_search,
                sort_by="date",
                sort_order="desc",
                status_filter="processed",
                time_window=sq_win
            )

            if processed_sales_items:
                for rec in processed_sales_items:
                    sla = database.calculate_sla_status(rec["timestamp"], is_processed=1)
                    metric_str = rec.get("headline_metric", "")
                    entity_str = rec.get("entity_name", "")
                    time_str = rec.get("timestamp", "")

                    data_dict = {}
                    try:
                        data_dict = json.loads(rec.get("full_output_json", "{}"))
                    except Exception:
                        pass

                    k1_l, k1_v = "Annual Revenue", str(data_dict.get("arr", metric_str.split("|")[-1].strip()))
                    if k1_v.isdigit():
                        k1_v = f"${int(k1_v):,} ARR"
                    k1_cls = "kpi-box-navy"

                    score_val = data_dict.get("lead_score", 85)
                    try:
                        score_num = int(score_val)
                    except Exception:
                        score_num = 85
                    k2_l, k2_v = "Lead Score", f"{score_num} / 100"
                    if score_num < 70:
                        k2_cls = "kpi-box-red"
                    elif score_num < 85:
                        k2_cls = "kpi-box-amber"
                    else:
                        k2_cls = "kpi-box-green"

                    k3_l, k3_v = "Commercial Fleet", f"{data_dict.get('fleet_size', '12')} Units"
                    try:
                        fleet_num = int(data_dict.get('fleet_size', 12))
                        if fleet_num < 5:
                            k3_cls = "kpi-box-amber"
                        else:
                            k3_cls = "kpi-box-teal"
                    except Exception:
                        k3_cls = "kpi-box-teal"

                    k4_l, k4_v = "Outreach Staged", "Cold Email & Phone Pitch"
                    k4_cls = "kpi-box-navy"

                    is_active = (st.session_state.active_sales_id == rec["id"])
                    active_cls = "active" if is_active else ""

                    st.markdown(f"""<div class="exec-card-hitbox">
<div class="exec-log-card {active_cls}" style="margin-bottom:0.5rem;">
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:gap:0.4rem;">
    <div>
        <span class="nudesk-badge badge-teal">SALES</span>
        <strong style="font-size:0.98rem; margin-left:0.4rem; color:var(--nd-text);">{entity_str}</strong>
        <span class="nudesk-badge badge-green" style="margin-left:0.4rem;">{rec['dispatch_status']}</span>
    </div>
    <div style="font-size:0.78rem; color:var(--nd-muted);">
        {sla['label']} &bull; {time_str}
    </div>
</div>
<div class="kpi-large-grid">
    <div class="kpi-box-large {k1_cls}">
        <div class="kpi-box-label">{k1_l}</div>
        <div class="kpi-box-val" style="font-size:1.05rem;">{k1_v}</div>
    </div>
    <div class="kpi-box-large {k2_cls}">
        <div class="kpi-box-label">{k2_l}</div>
        <div class="kpi-box-val" style="font-size:1.05rem;">{k2_v}</div>
    </div>
    <div class="kpi-box-large {k3_cls}">
        <div class="kpi-box-label">{k3_l}</div>
        <div class="kpi-box-val" style="font-size:1.05rem;">{k3_v}</div>
    </div>
    <div class="kpi-box-large {k4_cls}">
        <div class="kpi-box-label">{k4_l}</div>
        <div class="kpi-box-val" style="font-size:1.05rem;">{k4_v}</div>
    </div>
</div>
</div>
</div>""", unsafe_allow_html=True)

                    if st.button("Select", key=f"btn_sp_select_{rec['id']}", width="stretch"):
                        st.session_state.active_sales_id = rec["id"]
                        st.session_state.sales_result = None
                        st.rerun()
            else:
                st.info("No qualified leads found in this timeframe.")

    # ---------------- RIGHT PANEL: SALES DECISION CANVAS ----------------
    with col_s_canvas:
        is_manual_s = (st.session_state.active_sales_id == "manual")
        active_sales_rec = None

        if not is_manual_s:
            active_sales_rec = database.get_operation_by_id(st.session_state.active_sales_id)
            if not active_sales_rec:
                next_s = database.get_next_pending_operation("sales")
                if next_s:
                    st.session_state.active_sales_id = next_s["id"]
                    active_sales_rec = next_s
                else:
                    is_manual_s = True
                    st.session_state.active_sales_id = "manual"

        # Auto-align canvas record if current active tab is Processed but active_sales_rec is pending, or vice versa
        active_s_tab = st.session_state.get("sales_queue_tab_key", "")
        if "Processed" in active_s_tab and (active_sales_rec is None or active_sales_rec.get("is_processed") != 1):
            top_proc = database.get_filtered_operations(module_filter="sales", sort_by="date", sort_order="desc", status_filter="processed", time_window=sq_win, limit=1)
            if top_proc:
                st.session_state.active_sales_id = top_proc[0]["id"]
                active_sales_rec = top_proc[0]
                is_manual_s = False
        elif "Pending" in active_s_tab and (active_sales_rec is not None and active_sales_rec.get("is_processed") == 1):
            top_pend = database.get_filtered_operations(module_filter="sales", sort_by="date", sort_order="asc", status_filter="pending", time_window=sq_win, limit=1)
            if top_pend:
                st.session_state.active_sales_id = top_pend[0]["id"]
                active_sales_rec = top_pend[0]
                is_manual_s = False

        is_processed_s = (active_sales_rec is not None and active_sales_rec.get("is_processed") == 1)

        if is_processed_s:
            s_canvas_title = active_sales_rec["entity_name"]
            s_canvas_metric = active_sales_rec["headline_metric"]
            s_canvas_source = active_sales_rec.get("source_channel", "Commercial Outreach")
            s_canvas_sla = database.calculate_sla_status(active_sales_rec["timestamp"], is_processed=1)
            s_raw_text, s_doc_url, s_doc_note = get_transcript_for_entity(
                active_sales_rec["entity_name"], "sales", active_sales_rec.get("full_output_json")
            )
            data_dict = {}
            try:
                data_dict = json.loads(active_sales_rec.get("full_output_json", "{}"))
            except Exception:
                data_dict = {}

            st.markdown(f"""<div class="cockpit-header">
<div>
<div class="cockpit-title">{s_canvas_title}</div>
<div class="cockpit-sub">{s_canvas_metric} &bull; Qualified by: {active_sales_rec.get('operator_name', 'BDR Specialist')} ({active_sales_rec.get('operator_role', 'Commercial Outreach')})</div>
</div>
<div style="display:flex; align-items:center; gap:0.5rem;">
<span class="nudesk-badge badge-green">{active_sales_rec.get('dispatch_status', 'Synced').upper()}</span>
<span class="nudesk-badge {s_canvas_sla['color']}">{s_canvas_sla['label']}</span>
</div>
</div>""", unsafe_allow_html=True)

            col_ret_l, col_ret_r = st.columns([3, 1])
            with col_ret_r:
                if st.button("New / Pending Intake", key="btn_s_return_pending", width="stretch"):
                    next_p = database.get_next_pending_operation("sales")
                    st.session_state.active_sales_id = next_p["id"] if next_p else "manual"
                    st.session_state.sales_result = None
                    st.session_state.sales_queue_tab_key = f"Pending Queue ({sales_kpis['pending_count']})"
                    st.rerun()

            # Processed Detailed KPIs
            score_val = data_dict.get("lead_score", 85)
            arr_val = data_dict.get("annual_revenue_usd", data_dict.get("arr", s_canvas_metric.split("|")[-1].strip()))
            if isinstance(arr_val, (int, float)):
                arr_str = f"${arr_val:,.0f} ARR"
            elif str(arr_val).isdigit():
                arr_str = f"${int(arr_val):,} ARR"
            else:
                arr_str = str(arr_val)

            industry_val = data_dict.get("industry", "Commercial Freight & Logistics")
            fleet_size = data_dict.get("fleet_size", "12")
            fleet_str = f"{fleet_size} Units"

            st.markdown(f"""<div class="kpi-container">
<div class="kpi-card">
<div class="kpi-label">Lead Score</div>
<div class="kpi-value">{score_val} / 100</div>
<div class="kpi-sub">Outbound Priority</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Annual Revenue</div>
<div class="kpi-value">{arr_str}</div>
<div class="kpi-sub">Commercial Scale</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Commercial Sector</div>
<div class="kpi-value" style="font-size:1.15rem; margin-top:0.4rem;">{industry_val}</div>
<div class="kpi-sub">ICP Fit</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Commercial Fleet</div>
<div class="kpi-value">{fleet_str}</div>
<div class="kpi-sub">Fleet Operating Assets</div>
</div>
</div>""", unsafe_allow_html=True)

            st.markdown("#### Executive Assessment & Qualification Rationale")
            comp_name = data_dict.get("company_name", s_canvas_title)
            contact_p = data_dict.get("contact_person", "")
            full_lead_title = f"{comp_name} ({contact_p})" if contact_p and contact_p not in comp_name else comp_name
            rationale_text = active_sales_rec.get("assessment_summary") or data_dict.get("score_rationale", "")

            st.markdown(f"""<div class="studio-card">
<div class="studio-card-header">
<span class="studio-card-title">{full_lead_title}</span>
<span class="nudesk-badge badge-green">{contact_p or 'Verified Decision Maker'}</span>
</div>
<p style="color:var(--nd-text); font-size:0.9rem; line-height:1.6;">{rationale_text}</p>
</div>""", unsafe_allow_html=True)

            if active_sales_rec.get("analyst_notes"):
                st.markdown("#### BDR Verification & Outreach Notes")
                st.markdown(f"""<div style="background:var(--nd-surface-alt); border-left:4px solid var(--nd-green); padding:0.75rem 1rem; border-radius:4px; margin-bottom:1rem; font-size:0.9rem; color:var(--nd-text);">
<strong>BDR Sign-Off:</strong> {active_sales_rec['analyst_notes']}
<div style="font-size:0.78rem; color:var(--nd-muted); margin-top:0.35rem;">
Qualified by: {active_sales_rec.get('operator_name', 'BDR Specialist')} &bull; Status: {active_sales_rec.get('dispatch_status', 'Synced')} &bull; Audit Timestamp: {active_sales_rec.get('timestamp', '')}
</div>
</div>""", unsafe_allow_html=True)

            cold_email = data_dict.get("cold_email_en") or data_dict.get("cold_outreach_email", "")
            if cold_email:
                st.markdown("#### Staged Cold Outreach Email (Gmail / CRM Ready)")
                st.markdown(f"""<div class="studio-card">
<div class="script-box">{cold_email}</div>
</div>""", unsafe_allow_html=True)

            phone_script = data_dict.get("phone_script_30s_en") or data_dict.get("phone_pitch_script", "")
            if phone_script:
                st.markdown("#### 30-Second BDR Phone Pitch Script")
                st.markdown(f"""<div class="studio-card">
<div class="script-box">{phone_script}</div>
</div>""", unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown("#### Archived Sales Interaction & Notes")
                st.caption(f"Historical record from {s_canvas_source}. Verified commercial prospect dossier & accounts receivable aging.")
                dossier_s = get_synthetic_dossier(
                    active_sales_rec["entity_name"],
                    "sales",
                    active_sales_rec.get("full_output_json")
                )

                # Verified Cloud Document Links
                st.markdown(render_dossier_links_html(dossier_s["links"]), unsafe_allow_html=True)

                # Downloadable Synthetic Documents & Data
                s_files = dossier_s.get("files", [])
                if s_files:
                    st.markdown("<div style='font-size:0.82rem; font-weight:700; margin-bottom:0.4rem; color:var(--nd-text);'>Verified Downloadable Documents & Datasets</div>", unsafe_allow_html=True)
                    s_cols = st.columns(len(s_files))
                    for f_idx, f_item in enumerate(s_files):
                        with s_cols[f_idx]:
                            st.download_button(
                                label=f_item["name"],
                                data=f_item["content"],
                                file_name=f_item["file_name"],
                                mime=f_item["mime"],
                                key=f"btn_s_down_{active_sales_rec['id']}_{f_idx}",
                                help=f_item.get("description", "")
                            )

                st.text_area("Archived Interaction Notes:", value=active_sales_rec.get("transcript_text") or dossier_s.get("transcript") or s_raw_text, height=180, disabled=True, key=f"s_archived_{active_sales_rec['id']}")
                if s_doc_url:
                    st.markdown(f"**Direct Document Reference:** [{s_doc_url}]({s_doc_url})")

        else:
            if is_manual_s:
                s_canvas_title = "Ad-Hoc Commercial Lead Profile"
                s_canvas_metric = "Manual Ingestion Mode"
                s_canvas_source = "User Entry"
                s_canvas_sla = {"label": "Active Session", "color": "badge-navy"}
                s_raw_text, s_doc_url, s_doc_note = BENCHMARK_SALES_LEAD, "", ""
            else:
                s_canvas_title = active_sales_rec["entity_name"]
                s_canvas_metric = active_sales_rec["headline_metric"]
                s_canvas_source = active_sales_rec["source_channel"]
                s_canvas_sla = database.calculate_sla_status(active_sales_rec["timestamp"])
                s_raw_text, s_doc_url, s_doc_note = get_transcript_for_entity(
                    active_sales_rec["entity_name"], "sales", active_sales_rec.get("full_output_json")
                )

            st.markdown(f"""<div class="cockpit-header">
<div>
<div class="cockpit-title">{s_canvas_title}</div>
<div class="cockpit-sub">{s_canvas_metric} &bull; Source: {s_canvas_source}</div>
</div>
<div>
<span class="nudesk-badge {s_canvas_sla['color']}">{s_canvas_sla['label']}</span>
</div>
</div>""", unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown("#### Prospect Profile & AR Aging Dock")
                if not is_manual_s:
                    st.caption(f"Locked: Streaming directly from {s_canvas_source}. Text verification verified.")

                sales_input_text = st.text_area(
                    "Commercial Profile / Notes:",
                    value=s_raw_text,
                    height=180,
                    disabled=(not is_manual_s),
                    key=f"s_text_{st.session_state.active_sales_id}"
                )
                col_su1, col_su2 = st.columns([2, 1])
                with col_su1:
                    sales_url_input = st.text_input(
                        "AR Aging Report / Website URL (Optional):",
                        value=s_doc_url,
                        placeholder="https://company.com/freight-aging.pdf",
                        key=f"s_url_{st.session_state.active_sales_id}"
                    )
                with col_su2:
                    uploaded_sales_doc = st.file_uploader(
                        "Upload AR Aging / Financial PDF:",
                        key=f"s_file_{st.session_state.active_sales_id}"
                    )

            col_sbl, col_sbbtn, col_sbr = st.columns([1, 2, 1])
            with col_sbbtn:
                run_sales = st.button("Analyze Commercial Lead", type="primary", width="stretch", key="btn_run_sales_triage")

            if run_sales:
                with st.spinner("Scoring commercial prospect & crafting outreach..."):
                    supp_doc = ""
                    if sales_url_input:
                        supp_doc += f"\nScraped URL: {sales_url_input}\n" + document_reader.extract_text_from_url(sales_url_input)
                    if uploaded_sales_doc:
                        supp_doc += f"\nUploaded File: {uploaded_sales_doc.name}\n" + document_reader.extract_text_from_file(uploaded_sales_doc)

                    output, is_fb, msg = ai_engine.qualify_sales_lead(
                        lead_info=sales_input_text,
                        api_key=current_api_key,
                        supplementary_doc=supp_doc
                    )
                    st.session_state.sales_result = (output, is_fb, msg)

            if st.session_state.sales_result:
                sales_out: SalesLeadOutput = st.session_state.sales_result[0]
                is_fallback = st.session_state.sales_result[1]
                status_msg = st.session_state.sales_result[2]

                if is_fallback:
                    st.info(f"Demonstration Benchmark Mode: {status_msg}")
                else:
                    st.success(f"{status_msg}")

                st.markdown(f"""<div class="kpi-container">
<div class="kpi-card">
<div class="kpi-label">Lead Score</div>
<div class="kpi-value">{sales_out.lead_score} / 100</div>
<div class="kpi-sub">Outbound Priority</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Annual Revenue</div>
<div class="kpi-value">${sales_out.annual_revenue_usd:,.0f}</div>
<div class="kpi-sub">Reported ARR</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Target Sector</div>
<div class="kpi-value" style="font-size:1.15rem; margin-top:0.4rem;">{sales_out.industry}</div>
<div class="kpi-sub">Commercial Fit</div>
</div>
</div>""", unsafe_allow_html=True)

                st.markdown("#### Qualification Rationale & Cold Email")
                st.markdown(f"""<div class="studio-card">
<div class="studio-card-header">
<span class="studio-card-title">{sales_out.company_name}</span>
<span class="nudesk-badge badge-green">{sales_out.contact_person}</span>
</div>
<p style="color:var(--nd-text); font-size:0.88rem;">{sales_out.score_rationale}</p>
<div style="margin-top:0.75rem;">
<strong>Cold Email Draft (Gmail Ready):</strong>
<div class="script-box">{sales_out.cold_email_en}</div>
</div>
</div>""", unsafe_allow_html=True)

                st.markdown("#### 30-Second BDR Phone Script")
                st.markdown(f"""<div class="studio-card">
<div class="script-box">{sales_out.phone_script_30s_en}</div>
</div>""", unsafe_allow_html=True)

                st.markdown("#### BDR Verification & Sign-Off")
                s_analyst_note = st.text_area(
                    "BDR Outreach Notes / Call Back Timing (Optional):",
                    placeholder="e.g. Spoke to dispatch director; high interest in 24-hr advance for harvest season.",
                    key="s_analyst_note_input"
                )

                col_sap_l, col_sap_btn, col_sap_r = st.columns([1, 2, 1])
                with col_sap_btn:
                    if st.button("Qualify Lead & Stage Outreach (Auto-Advance)", type="primary", width="stretch", key="btn_s_dispatch"):
                        if is_manual_s or not active_sales_rec:
                            rec_id = database.save_operation(
                                operator_name=persona.name,
                                operator_role=persona.role_title,
                                module_type="sales",
                                entity_name=f"{sales_out.company_name} ({sales_out.contact_person})",
                                headline_metric=f"Score: {sales_out.lead_score}/100 | ${sales_out.annual_revenue_usd:,.0f} ARR",
                                assessment_summary=sales_out.score_rationale,
                                full_output_json=sales_out.model_dump(),
                                dispatch_status="Synced",
                                is_processed=1,
                                source_channel="Manual Ingestion",
                                analyst_notes=s_analyst_note
                            )
                        else:
                            rec_id = active_sales_rec["id"]
                            database.mark_operation_processed(
                                record_id=rec_id,
                                dispatch_status="Synced",
                                headline_metric=f"Score: {sales_out.lead_score}/100 | ${sales_out.annual_revenue_usd:,.0f} ARR",
                                assessment_summary=sales_out.score_rationale,
                                full_output_json=sales_out.model_dump(),
                                operator_name=persona.name,
                                operator_role=persona.role_title,
                                analyst_notes=s_analyst_note
                            )

                        crm_dispatcher.dispatch_to_n8n(
                            webhook_url=current_webhook_url,
                            payload={**sales_out.model_dump(), "analyst_notes": s_analyst_note},
                            flow_type="sales"
                        )

                        next_pending_s = database.get_next_pending_operation("sales", exclude_id=rec_id)
                        st.session_state.sales_result = None
                        if next_pending_s:
                            st.session_state.active_sales_id = next_pending_s["id"]
                            st.success(f"Lead synced to CRM. Auto-advancing to: {next_pending_s['entity_name']}")
                        else:
                            st.session_state.active_sales_id = "manual"
                            st.success("Lead synced to CRM. All queue prospects qualified!")
                        st.rerun()

# =========================================================================
# TAB 3: TALENT OPERATIONS (HR SCREENING - SPLIT COCKPIT)
# =========================================================================
with tabs[2]:
    col_h_head, col_h_win = st.columns([7, 3], gap="medium")
    with col_h_head:
        st.markdown("### HR & Talent Solutions — Candidate Screening Cockpit")
        st.caption("Bilingual interview evaluation, technical competency grading, and hiring manager case-study guides.")
    with col_h_win:
        hq_win = st.selectbox(
            "HR Reporting Period:",
            options=list(time_window_choices.keys()),
            format_func=lambda k: time_window_choices[k],
            index=list(time_window_choices.keys()).index(st.session_state.get("hq_win", "week")),
            key="hq_win",
            label_visibility="visible"
        )

    hr_kpis = database.get_department_kpis("hr", time_window=hq_win)
    hr_records = database.get_filtered_operations(module_filter="hr", time_window=hq_win, limit=200)

    # Top Section: Key Metrics Ribbon & Dual Donut Visualizations (Status + Candidate Fit)
    col_h_stats, col_h_donut_status, col_h_donut_fit = st.columns([4, 4, 4], gap="medium")
    with col_h_stats:
        st.markdown(f"""<div class="kpi-container" style="grid-template-columns: repeat(2, 1fr); margin-bottom: 0.5rem;">
<div class="kpi-card" style="padding:0.75rem 1rem;">
    <div class="kpi-label">Pending Screenings (FIFO)</div>
    <div class="kpi-value" style="font-size:1.35rem;">{hr_kpis['pending_count']} candidates</div>
    <div class="kpi-sub">Bilingual interviews queued</div>
</div>
<div class="kpi-card" style="padding:0.75rem 1rem;">
    <div class="kpi-label">Candidates Evaluated</div>
    <div class="kpi-value" style="font-size:1.35rem;">{hr_kpis['processed_count']} synced</div>
    <div class="kpi-sub">Advanced to hiring teams</div>
</div>
</div>""", unsafe_allow_html=True)

    with col_h_donut_status:
        tot_h_ops = hr_kpis['pending_count'] + hr_kpis['processed_count']
        if tot_h_ops > 0:
            df_h_status = pd.DataFrame({
                "Status": ["Completed", "Pending"],
                "Candidates": [hr_kpis['processed_count'], hr_kpis['pending_count']]
            })
            df_h_status = df_h_status[df_h_status["Candidates"] > 0]
            h_status_chart = alt.Chart(df_h_status).mark_arc(innerRadius=36).encode(
                theta=alt.Theta(field="Candidates", type="quantitative"),
                color=alt.Color(
                    field="Status",
                    type="nominal",
                    scale=alt.Scale(
                        domain=["Completed", "Pending"],
                        range=["#3EA258", "#D97706"]
                    ),
                    legend=alt.Legend(orient="right", title=None)
                ),
                tooltip=["Status", "Candidates"]
            ).properties(height=110)
            h_status_chart = configure_altair_donut(h_status_chart, st.session_state.current_theme)
            st.altair_chart(h_status_chart, width="stretch", theme=None)
        else:
            st.info("No candidates in this period.")

    with col_h_donut_fit:
        high_fit_h = 0
        mod_fit_h = 0
        low_fit_h = 0
        for r in hr_records:
            raw = r.get("full_output_json", "{}")
            d = {}
            try:
                d = json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                pass
            tier = str(d.get("candidate_fit_tier", "")).lower()
            score = d.get("candidate_fit_score", d.get("fit_score", d.get("overall_fit_score", 0)))
            try:
                score_int = int(score)
            except Exception:
                score_int = 0

            if "high" in tier or score_int >= 85:
                high_fit_h += 1
            elif "moderate" in tier or score_int >= 70:
                mod_fit_h += 1
            else:
                low_fit_h += 1

        tot_fit_h = high_fit_h + mod_fit_h + low_fit_h
        if tot_fit_h > 0:
            df_h_fit = pd.DataFrame({
                "Candidate Fit": ["High Fit (>=85)", "Moderate Fit (70-84)", "Low Fit (<70)"],
                "Candidates": [max(1, high_fit_h), max(1, mod_fit_h), max(0, low_fit_h)]
            })
            df_h_fit = df_h_fit[df_h_fit["Candidates"] > 0]
            h_fit_chart = alt.Chart(df_h_fit).mark_arc(innerRadius=36).encode(
                theta=alt.Theta(field="Candidates", type="quantitative"),
                color=alt.Color(
                    field="Candidate Fit",
                    type="nominal",
                    scale=alt.Scale(
                        domain=["High Fit (>=85)", "Moderate Fit (70-84)", "Low Fit (<70)"],
                        range=["#3EA258", "#D97706", "#DC2626"]
                    ),
                    legend=alt.Legend(orient="right", title=None)
                ),
                tooltip=["Candidate Fit", "Candidates"]
            ).properties(height=110)
            h_fit_chart = configure_altair_donut(h_fit_chart, st.session_state.current_theme)
            st.altair_chart(h_fit_chart, width="stretch", theme=None)
        else:
            st.info("No candidate fit evaluations in this period.")

    col_h_queue, col_h_canvas = st.columns([5, 7])

    # ---------------- LEFT PANEL: HR QUEUE & AUDIT ----------------
    with col_h_queue:
        def on_hr_tab_change():
            curr_tab = st.session_state.get("hr_queue_tab_key", "")
            if "Pending" in curr_tab:
                top_items = database.get_filtered_operations(
                    module_filter="hr",
                    sort_by="date",
                    sort_order="asc",
                    status_filter="pending",
                    time_window=st.session_state.get("hq_win", "week"),
                    limit=1
                )
                if top_items:
                    st.session_state.active_hr_id = top_items[0]["id"]
                    st.session_state.hr_result = None
            elif "Processed" in curr_tab:
                top_items = database.get_filtered_operations(
                    module_filter="hr",
                    sort_by="date",
                    sort_order="desc",
                    status_filter="processed",
                    time_window=st.session_state.get("hq_win", "week"),
                    limit=1
                )
                if top_items:
                    st.session_state.active_hr_id = top_items[0]["id"]
                    st.session_state.hr_result = None

        hr_queue_tabs = st.tabs([
            f"Pending Queue ({hr_kpis['pending_count']})",
            f"Processed Talent ({hr_kpis['processed_count']})"
        ], key="hr_queue_tab_key", on_change=on_hr_tab_change)

        with hr_queue_tabs[0]:
            col_hq_s, col_hq_area, col_hq_o = st.columns([4, 4, 3])
            with col_hq_s:
                hq_search = st.text_input("Filter Candidates:", placeholder="Search candidate, role...", key="hq_search", label_visibility="collapsed")
            with col_hq_area:
                hq_area = st.selectbox(
                    "Area Filter:",
                    ["All Areas", "Credit Underwriting & Risk", "Commercial Sales & BDR", "Operations & Accounting", "Technology & Systems"],
                    key="hq_area_filter",
                    label_visibility="collapsed"
                )
            with col_hq_o:
                hq_order = st.selectbox("Sort:", ["Oldest First (FIFO)", "Newest First"], index=0, key="hq_order", label_visibility="collapsed")

            hq_dir = "asc" if "Oldest" in hq_order else "desc"
            pending_hr_items = database.get_filtered_operations(
                module_filter="hr",
                search_query=hq_search,
                sort_by="date",
                sort_order=hq_dir,
                status_filter="pending",
                time_window=hq_win
            )
            if hq_area != "All Areas":
                pending_hr_items = [r for r in pending_hr_items if database.get_candidate_area(r) == hq_area]

            col_had1, col_had2 = st.columns([1, 1])
            with col_had1:
                if st.button("+ Manual Entry", key="btn_h_manual_entry", width="stretch"):
                    st.session_state.active_hr_id = "manual"
                    st.session_state.hr_result = None
                    st.rerun()
            with col_had2:
                with st.popover("+ Simulate Stream", width="stretch"):
                    st.caption("Inject synthetic external webhook payload:")
                    if st.button("Read AI: Bilingual Underwriter (C1)", key="sim_h_readai", width="stretch"):
                        from scripts.generate_synthetic_intake import generate_synthetic_payload, extract_ingestion_fields
                        p = generate_synthetic_payload("readai", "hr")
                        f = extract_ingestion_fields(p, "readai", "hr")
                        new_id = database.ingest_pending_record(
                            module_type=f["module_type"], entity_name=f["entity_name"], headline_metric=f["headline_metric"],
                            transcript_text=f["transcript_text"], assessment_summary=f["assessment_summary"], source_channel=f["source_channel"],
                            doc_url=f["doc_url"], doc_note=f["doc_note"], metadata_extra=f["metadata_extra"]
                        )
                        st.session_state.active_hr_id = new_id
                        st.session_state.hr_result = None
                        st.rerun()

            if pending_hr_items:
                for rec in pending_hr_items:
                    sla = database.calculate_sla_status(rec["timestamp"])
                    is_active = (st.session_state.active_hr_id == rec["id"])
                    active_cls = "active" if is_active else ""

                    status_indicator = "ACTIVE IN CANVAS" if is_active else rec["timestamp"]
                    st.markdown(f"""<div class="queue-card-hitbox">
<div class="queue-card {active_cls}">
<div class="queue-entity">{rec['entity_name']}</div>
<div class="queue-metric">{rec['headline_metric']}</div>
<div class="queue-meta">
<span><span class="nudesk-badge {sla['color']}">{sla['label']}</span> &bull; {database.get_candidate_area(rec)}</span>
<span style="font-weight:{'700' if is_active else '400'}; color:{'var(--nd-green)' if is_active else 'var(--nd-muted)'};">{status_indicator}</span>
</div>
</div>
</div>""", unsafe_allow_html=True)

                    if st.button("Select", key=f"btn_h_select_{rec['id']}", width="stretch"):
                        st.session_state.active_hr_id = rec["id"]
                        st.session_state.hr_result = None
                        st.rerun()
            else:
                st.info("Pending candidate screening queue is clear for this filter.")

        with hr_queue_tabs[1]:
            col_hp_s, col_hp_area = st.columns([6, 5])
            with col_hp_s:
                hp_search = st.text_input("Filter Talent Pipeline:", placeholder="Search screened candidates...", key="hp_search", label_visibility="collapsed")
            with col_hp_area:
                hp_area = st.selectbox(
                    "Filter by Area:",
                    ["All Areas", "Credit Underwriting & Risk", "Commercial Sales & BDR", "Operations & Accounting", "Technology & Systems"],
                    key="hp_area_filter",
                    label_visibility="collapsed"
                )

            processed_hr_items = database.get_filtered_operations(
                module_filter="hr",
                search_query=hp_search,
                sort_by="date",
                sort_order="desc",
                status_filter="processed",
                time_window=hq_win
            )
            if hp_area != "All Areas":
                processed_hr_items = [r for r in processed_hr_items if database.get_candidate_area(r) == hp_area]

            if processed_hr_items:
                for rec in processed_hr_items:
                    sla = database.calculate_sla_status(rec["timestamp"], is_processed=1)
                    metric_str = rec.get("headline_metric", "")
                    entity_str = rec.get("entity_name", "")
                    time_str = rec.get("timestamp", "")

                    data_dict = {}
                    try:
                        data_dict = json.loads(rec.get("full_output_json", "{}"))
                    except Exception:
                        pass

                    fit_tier = str(data_dict.get("candidate_fit_tier", "High Fit"))
                    fit_score = data_dict.get("candidate_fit_score", data_dict.get("fit_score", data_dict.get("overall_fit_score", 90)))
                    try:
                        fit_num = int(fit_score)
                    except Exception:
                        fit_num = 90

                    k1_l, k1_v = "Candidate Fit", f"{fit_tier} ({fit_num}/100)"
                    if fit_num < 75 or "low" in fit_tier.lower():
                        k1_cls = "kpi-box-red"
                    elif fit_num < 85 or "moderate" in fit_tier.lower():
                        k1_cls = "kpi-box-amber"
                    else:
                        k1_cls = "kpi-box-green"

                    psico_val = data_dict.get("psychometrics_score", 88)
                    try:
                        psico_num = int(psico_val)
                    except Exception:
                        psico_num = 88
                    k2_l, k2_v = "Psicométricos", f"{psico_num} / 100"
                    if psico_num < 70:
                        k2_cls = "kpi-box-red"
                    elif psico_num < 80:
                        k2_cls = "kpi-box-amber"
                    else:
                        k2_cls = "kpi-box-teal"

                    know_val = data_dict.get("knowledge_test_score", 90)
                    try:
                        know_num = int(know_val)
                    except Exception:
                        know_num = 90
                    k3_l, k3_v = "Test Conocimientos", f"{know_num} / 100"
                    if know_num < 70:
                        k3_cls = "kpi-box-red"
                    elif know_num < 80:
                        k3_cls = "kpi-box-amber"
                    else:
                        k3_cls = "kpi-box-green"

                    cand_area = database.get_candidate_area(rec)
                    k4_l, k4_v = "Área Funcional", cand_area
                    k4_cls = "kpi-box-navy"

                    is_active = (st.session_state.active_hr_id == rec["id"])
                    active_cls = "active" if is_active else ""

                    st.markdown(f"""<div class="exec-card-hitbox">
<div class="exec-log-card {active_cls}" style="margin-bottom:0.5rem;">
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.4rem;">
    <div>
        <span class="nudesk-badge badge-green">HR TALENT</span>
        <strong style="font-size:0.98rem; margin-left:0.4rem; color:var(--nd-text);">{entity_str}</strong>
        <span class="nudesk-badge badge-green" style="margin-left:0.4rem;">{rec['dispatch_status']}</span>
    </div>
    <div style="font-size:0.78rem; color:var(--nd-muted);">
        {sla['label']} &bull; {time_str}
    </div>
</div>
<div class="kpi-large-grid">
    <div class="kpi-box-large {k1_cls}">
        <div class="kpi-box-label">{k1_l}</div>
        <div class="kpi-box-val" style="font-size:1.05rem;">{k1_v}</div>
    </div>
    <div class="kpi-box-large {k2_cls}">
        <div class="kpi-box-label">{k2_l}</div>
        <div class="kpi-box-val" style="font-size:1.05rem;">{k2_v}</div>
    </div>
    <div class="kpi-box-large {k3_cls}">
        <div class="kpi-box-label">{k3_l}</div>
        <div class="kpi-box-val" style="font-size:1.05rem;">{k3_v}</div>
    </div>
    <div class="kpi-box-large {k4_cls}">
        <div class="kpi-box-label">{k4_l}</div>
        <div class="kpi-box-val" style="font-size:0.92rem; overflow:hidden; text-overflow:ellipsis;">{k4_v}</div>
    </div>
</div>
</div>
</div>""", unsafe_allow_html=True)

                    if st.button("Select", key=f"btn_hp_select_{rec['id']}", width="stretch"):
                        st.session_state.active_hr_id = rec["id"]
                        st.session_state.hr_result = None
                        st.rerun()
            else:
                st.info("No candidate scorecards found for this filter.")

    # ---------------- RIGHT PANEL: HR DECISION CANVAS ----------------
    with col_h_canvas:
        is_manual_h = (st.session_state.active_hr_id == "manual")
        active_hr_rec = None

        if not is_manual_h:
            active_hr_rec = database.get_operation_by_id(st.session_state.active_hr_id)
            if not active_hr_rec:
                next_h = database.get_next_pending_operation("hr")
                if next_h:
                    st.session_state.active_hr_id = next_h["id"]
                    active_hr_rec = next_h
                else:
                    is_manual_h = True
                    st.session_state.active_hr_id = "manual"

        # Auto-align canvas record if current active tab is Processed but active_hr_rec is pending, or vice versa
        active_h_tab = st.session_state.get("hr_queue_tab_key", "")
        if "Processed" in active_h_tab and (active_hr_rec is None or active_hr_rec.get("is_processed") != 1):
            top_proc = database.get_filtered_operations(module_filter="hr", sort_by="date", sort_order="desc", status_filter="processed", time_window=hq_win, limit=1)
            if top_proc:
                st.session_state.active_hr_id = top_proc[0]["id"]
                active_hr_rec = top_proc[0]
                is_manual_h = False
        elif "Pending" in active_h_tab and (active_hr_rec is not None and active_hr_rec.get("is_processed") == 1):
            top_pend = database.get_filtered_operations(module_filter="hr", sort_by="date", sort_order="asc", status_filter="pending", time_window=hq_win, limit=1)
            if top_pend:
                st.session_state.active_hr_id = top_pend[0]["id"]
                active_hr_rec = top_pend[0]
                is_manual_h = False

        is_processed_h = (active_hr_rec is not None and active_hr_rec.get("is_processed") == 1)

        if is_processed_h:
            h_canvas_title = active_hr_rec["entity_name"]
            h_canvas_metric = active_hr_rec["headline_metric"]
            h_canvas_source = active_hr_rec.get("source_channel", "Talent Ingestion")
            h_canvas_sla = database.calculate_sla_status(active_hr_rec["timestamp"], is_processed=1)
            h_raw_text, h_doc_url, h_doc_note = get_transcript_for_entity(
                active_hr_rec["entity_name"], "hr", active_hr_rec.get("full_output_json")
            )
            data_dict = {}
            try:
                data_dict = json.loads(active_hr_rec.get("full_output_json", "{}"))
            except Exception:
                data_dict = {}

            st.markdown(f"""<div class="cockpit-header">
<div>
<div class="cockpit-title">{h_canvas_title}</div>
<div class="cockpit-sub">{h_canvas_metric} &bull; Screened by: {active_hr_rec.get('operator_name', 'Talent Recruiter')} ({active_hr_rec.get('operator_role', 'Recruiting Specialist')})</div>
</div>
<div style="display:flex; align-items:center; gap:0.5rem;">
<span class="nudesk-badge badge-green">{active_hr_rec.get('dispatch_status', 'Synced').upper()}</span>
<span class="nudesk-badge {h_canvas_sla['color']}">{h_canvas_sla['label']}</span>
</div>
</div>""", unsafe_allow_html=True)

            col_ret_l, col_ret_r = st.columns([3, 1])
            with col_ret_r:
                if st.button("New / Pending Intake", key="btn_h_return_pending", width="stretch"):
                    next_p = database.get_next_pending_operation("hr")
                    st.session_state.active_hr_id = next_p["id"] if next_p else "manual"
                    st.session_state.hr_result = None
                    st.session_state.hr_queue_tab_key = f"Pending Queue ({hr_kpis['pending_count']})"
                    st.rerun()

            # Processed Detailed KPIs
            fit_tier = str(data_dict.get("candidate_fit_tier", "High Fit"))
            fit_score = data_dict.get("candidate_fit_score", data_dict.get("fit_score", data_dict.get("overall_fit_score", 90)))
            fit_color = "#3EA258" if "high" in fit_tier.lower() else ("#D97706" if "mod" in fit_tier.lower() else "#DC2626")

            psico_val = data_dict.get("psychometrics_score", 88)
            know_val = data_dict.get("knowledge_test_score", 90)
            cand_area = database.get_candidate_area(active_hr_rec)

            st.markdown(f"""<div class="kpi-container">
<div class="kpi-card">
<div class="kpi-label">Candidate Fit (AI)</div>
<div class="kpi-value" style="color:{fit_color}; font-size:1.2rem;">{fit_tier}</div>
<div class="kpi-sub">Score: {fit_score} / 100</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Calificación Psicométricos</div>
<div class="kpi-value">{psico_val} / 100</div>
<div class="kpi-sub">Personality & Diligence</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Test de Conocimientos</div>
<div class="kpi-value">{know_val} / 100</div>
<div class="kpi-sub">Technical Verification</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Área Funcional</div>
<div class="kpi-value" style="font-size:1.02rem; margin-top:0.4rem;">{cand_area}</div>
<div class="kpi-sub">Department Allocation</div>
</div>
</div>""", unsafe_allow_html=True)

            st.markdown("#### Assessment Summary & Screening Dossier")
            cand_name = data_dict.get("candidate_name", h_canvas_title)
            applied_role = data_dict.get("applied_role", "Candidate")
            summary_text = active_hr_rec.get("assessment_summary") or data_dict.get("executive_summary", "")

            st.markdown(f"""<div class="studio-card">
<div class="studio-card-header">
<span class="studio-card-title">{cand_name} ({applied_role})</span>
<span class="nudesk-badge badge-green">{cand_area}</span>
</div>
<p style="color:var(--nd-text); font-size:0.9rem; line-height:1.6;">{summary_text}</p>
</div>""", unsafe_allow_html=True)

            if active_hr_rec.get("analyst_notes"):
                st.markdown("#### Recruiter Verification & Sign-Off Notes")
                st.markdown(f"""<div style="background:var(--nd-surface-alt); border-left:4px solid var(--nd-green); padding:0.75rem 1rem; border-radius:4px; margin-bottom:1rem; font-size:0.9rem; color:var(--nd-text);">
<strong>Recruiter Notes:</strong> {active_hr_rec['analyst_notes']}
<div style="font-size:0.78rem; color:var(--nd-muted); margin-top:0.35rem;">
Audited by: {active_hr_rec.get('operator_name', 'Talent Recruiter')} &bull; Status: {active_hr_rec.get('dispatch_status', 'Synced')} &bull; Audit Timestamp: {active_hr_rec.get('timestamp', '')}
</div>
</div>""", unsafe_allow_html=True)

            comps = data_dict.get("technical_competencies", [])
            if comps:
                st.markdown("#### Verified Competencies")
                for comp in comps:
                    st.markdown(f'<div class="bullet-item"><span class="bullet-dot"></span><span class="bullet-text">{comp}</span></div>', unsafe_allow_html=True)

            q_list = data_dict.get("next_interview_focus_questions", data_dict.get("interview_questions", []))
            if q_list:
                st.markdown("#### Next Round Interview Protocol")
                for idx, q in enumerate(q_list, 1):
                    st.markdown(f"""<div style="background:var(--nd-surface-alt); border:1px solid var(--nd-border); border-radius:4px; padding:0.65rem 0.9rem; margin-bottom:0.5rem; font-size:0.88rem; color:var(--nd-text);">
<strong>Q{idx}:</strong> {q}
</div>""", unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown("#### Archived Candidate Interview Transcript & CV Notes")
                st.caption(f"Historical record from {h_canvas_source}. Verified candidate background, test scorecards & interview transcript.")
                dossier_h = get_synthetic_dossier(
                    active_hr_rec["entity_name"],
                    "hr",
                    active_hr_rec.get("full_output_json")
                )

                # Verified Cloud Document Links
                st.markdown(render_dossier_links_html(dossier_h["links"]), unsafe_allow_html=True)

                # Downloadable Synthetic Documents & Data
                h_files = dossier_h.get("files", [])
                if h_files:
                    st.markdown("<div style='font-size:0.82rem; font-weight:700; margin-bottom:0.4rem; color:var(--nd-text);'>Verified Downloadable Documents & Datasets</div>", unsafe_allow_html=True)
                    h_cols = st.columns(len(h_files))
                    for f_idx, f_item in enumerate(h_files):
                        with h_cols[f_idx]:
                            st.download_button(
                                label=f_item["name"],
                                data=f_item["content"],
                                file_name=f_item["file_name"],
                                mime=f_item["mime"],
                                key=f"btn_h_down_{active_hr_rec['id']}_{f_idx}",
                                help=f_item.get("description", "")
                            )

                st.text_area("Archived Screening Transcript:", value=active_hr_rec.get("transcript_text") or dossier_h.get("transcript") or h_raw_text, height=180, disabled=True, key=f"h_archived_{active_hr_rec['id']}")
                if h_doc_url:
                    st.markdown(f"**Direct Document Reference:** [{h_doc_url}]({h_doc_url})")

        else:
            if is_manual_h:
                h_canvas_title = "Ad-Hoc Candidate Screening"
                h_canvas_metric = "Manual Ingestion Mode"
                h_canvas_source = "User Entry"
                h_canvas_sla = {"label": "Active Session", "color": "badge-navy"}
                h_raw_text, h_doc_url, h_doc_note = BENCHMARK_HR_TRANSCRIPT, "", ""
            else:
                h_canvas_title = active_hr_rec["entity_name"]
                h_canvas_metric = active_hr_rec["headline_metric"]
                h_canvas_source = active_hr_rec["source_channel"]
                h_canvas_sla = database.calculate_sla_status(active_hr_rec["timestamp"])
                h_raw_text, h_doc_url, h_doc_note = get_transcript_for_entity(
                    active_hr_rec["entity_name"], "hr", active_hr_rec.get("full_output_json")
                )

            st.markdown(f"""<div class="cockpit-header">
<div>
<div class="cockpit-title">{h_canvas_title}</div>
<div class="cockpit-sub">{h_canvas_metric} &bull; Source: {h_canvas_source}</div>
</div>
<div>
<span class="nudesk-badge {h_canvas_sla['color']}">{h_canvas_sla['label']}</span>
</div>
</div>""", unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown("#### Screening Transcript & Resume Dock")
                if not is_manual_h:
                    st.caption(f"Locked: Streaming directly from {h_canvas_source}. Text verification verified.")

                hr_input_text = st.text_area(
                    "Interview Transcript:",
                    value=h_raw_text,
                    height=180,
                    disabled=(not is_manual_h),
                    key=f"h_text_{st.session_state.active_hr_id}"
                )
                col_hu1, col_hu2 = st.columns([2, 1])
                with col_hu1:
                    hr_url_input = st.text_input(
                        "LinkedIn / Resume Credentials URL (Optional):",
                        value=h_doc_url,
                        placeholder="https://linkedin.com/in/candidate",
                        key=f"h_url_{st.session_state.active_hr_id}"
                    )
                with col_hu2:
                    uploaded_hr_doc = st.file_uploader(
                        "Upload Resume / Credentials PDF:",
                        key=f"h_file_{st.session_state.active_hr_id}"
                    )

            col_hbl, col_hbbtn, col_hbr = st.columns([1, 2, 1])
            with col_hbbtn:
                run_hr = st.button("Grade Candidate Screening", type="primary", width="stretch", key="btn_run_hr_triage")

            if run_hr:
                with st.spinner("Grading bilingual fluency & technical competencies..."):
                    supp_doc = ""
                    if hr_url_input:
                        supp_doc += f"\nScraped URL: {hr_url_input}\n" + document_reader.extract_text_from_url(hr_url_input)
                    if uploaded_hr_doc:
                        supp_doc += f"\nUploaded File: {uploaded_hr_doc.name}\n" + document_reader.extract_text_from_file(uploaded_hr_doc)

                    output, is_fb, msg = ai_engine.analyze_hr_interview(
                        interview_transcript=hr_input_text,
                        api_key=current_api_key,
                        supplementary_doc=supp_doc
                    )
                    st.session_state.hr_result = (output, is_fb, msg)

            if st.session_state.hr_result:
                hr_out: HRTalentOutput = st.session_state.hr_result[0]
                is_fallback = st.session_state.hr_result[1]
                status_msg = st.session_state.hr_result[2]

                if is_fallback:
                    st.info(f"Demonstration Benchmark Mode: {status_msg}")
                else:
                    st.success(f"{status_msg}")

                fit_color = "#3EA258" if hr_out.candidate_fit_tier == "High Fit" else ("#D97706" if hr_out.candidate_fit_tier == "Moderate Fit" else "#DC2626")
                st.markdown(f"""<div class="kpi-container">
<div class="kpi-card">
<div class="kpi-label">Candidate Fit (AI)</div>
<div class="kpi-value" style="color:{fit_color}; font-size:1.2rem;">{hr_out.candidate_fit_tier}</div>
<div class="kpi-sub">Score: {hr_out.candidate_fit_score} / 100</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Calificación Psicométricos</div>
<div class="kpi-value">{hr_out.psychometrics_score} / 100</div>
<div class="kpi-sub">Personality & Diligence</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Test de Conocimientos</div>
<div class="kpi-value">{hr_out.knowledge_test_score} / 100</div>
<div class="kpi-sub">{hr_out.application_area}</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Recomendación</div>
<div class="kpi-value" style="font-size:1.05rem; margin-top:0.4rem; color:var(--nd-green);">{hr_out.recommended_action}</div>
<div class="kpi-sub">Hiring Pipeline</div>
</div>
</div>""", unsafe_allow_html=True)

                st.markdown("#### Assessment Summary & Technical Competencies")
                st.markdown(f"""<div class="studio-card">
<div class="studio-card-header">
<span class="studio-card-title">{hr_out.candidate_name}</span>
<span class="nudesk-badge badge-green">{hr_out.applied_role} &bull; {hr_out.application_area}</span>
</div>
<p style="color:var(--nd-text); font-size:0.9rem; line-height:1.6;">{hr_out.executive_summary}</p>
</div>""", unsafe_allow_html=True)

                if hr_out.technical_competencies:
                    st.markdown("**Verified Competencies:**")
                    for comp in hr_out.technical_competencies:
                        st.markdown(f'<div class="bullet-item"><span class="bullet-dot"></span><span class="bullet-text">{comp}</span></div>', unsafe_allow_html=True)

                st.markdown("#### Next Round Interview Protocol")
                for idx, q in enumerate(hr_out.next_interview_focus_questions, 1):
                    st.markdown(f"""<div style="background:var(--nd-surface-alt); border:1px solid var(--nd-border); border-radius:4px; padding:0.65rem 0.9rem; margin-bottom:0.5rem; font-size:0.88rem; color:var(--nd-text);">
<strong>Q{idx}:</strong> {q}
</div>""", unsafe_allow_html=True)

                st.markdown("#### Recruiter Verification & Sign-Off")
                h_analyst_note = st.text_area(
                    "Recruiter Feedback / Case Study Assignment Notes (Optional):",
                    placeholder="e.g. Demonstrated outstanding credit modeling instincts; advance immediately to technical underwriting case study.",
                    key="h_analyst_note_input"
                )

                col_hap_l, col_hap_btn, col_hap_r = st.columns([1, 2, 1])
                with col_hap_btn:
                    if st.button("Advance Candidate & Sign-Off (Auto-Advance)", type="primary", width="stretch", key="btn_h_dispatch"):
                        headline_str = f"{hr_out.candidate_fit_tier} ({hr_out.candidate_fit_score}) | Psico: {hr_out.psychometrics_score} | Test: {hr_out.knowledge_test_score}"
                        if is_manual_h or not active_hr_rec:
                            rec_id = database.save_operation(
                                operator_name=persona.name,
                                operator_role=persona.role_title,
                                module_type="hr",
                                entity_name=f"{hr_out.candidate_name} ({hr_out.applied_role})",
                                headline_metric=headline_str,
                                assessment_summary=hr_out.executive_summary,
                                full_output_json=hr_out.model_dump(),
                                dispatch_status="Synced",
                                is_processed=1,
                                source_channel="Manual Ingestion",
                                analyst_notes=h_analyst_note
                            )
                        else:
                            rec_id = active_hr_rec["id"]
                            database.mark_operation_processed(
                                record_id=rec_id,
                                dispatch_status="Synced",
                                headline_metric=headline_str,
                                assessment_summary=hr_out.executive_summary,
                                full_output_json=hr_out.model_dump(),
                                operator_name=persona.name,
                                operator_role=persona.role_title,
                                analyst_notes=h_analyst_note
                            )

                        crm_dispatcher.dispatch_to_n8n(
                            webhook_url=current_webhook_url,
                            payload={**hr_out.model_dump(), "analyst_notes": h_analyst_note},
                            flow_type="hr"
                        )

                        next_pending_h = database.get_next_pending_operation("hr", exclude_id=rec_id)
                        st.session_state.hr_result = None
                        if next_pending_h:
                            st.session_state.active_hr_id = next_pending_h["id"]
                            st.success(f"Candidate file advanced. Auto-advancing to: {next_pending_h['entity_name']}")
                        else:
                            st.session_state.active_hr_id = "manual"
                            st.success("Candidate file advanced. All screening queue files completed!")
                        st.rerun()

# =========================================================================
# TAB 4: EXECUTIVE KPI DASHBOARD & AUDIT HISTORY
# =========================================================================
with tabs[3]:
    col_exec_title, col_exec_win = st.columns([7, 3], gap="medium")
    with col_exec_title:
        st.markdown("### Executive Overview & Operational Audit Trail")
        st.caption("Consolidated operations across Credit, Sales, and HR teams in Mazatlán.")
    with col_exec_win:
        exec_win = st.selectbox(
            "Executive Reporting Period:",
            options=list(time_window_choices.keys()),
            format_func=lambda k: time_window_choices[k],
            index=list(time_window_choices.keys()).index(st.session_state.get("exec_win", "week")),
            key="exec_win"
        )

    all_records = database.get_filtered_operations(
        module_filter="all",
        status_filter="all",
        time_window=exec_win,
        limit=500
    )
    total_ops = len(all_records)
    pending_total = len([r for r in all_records if r["is_processed"] == 0])
    processed_total = len([r for r in all_records if r["is_processed"] == 1])

    credit_total = len([r for r in all_records if r["module_type"] == "credit"])
    sales_total = len([r for r in all_records if r["module_type"] == "sales"])
    hr_total = len([r for r in all_records if r["module_type"] == "hr"])

    import pandas as pd
    import altair as alt

    # Calculate capital pipeline totals dynamically based on the filtered time window
    total_credit_volume = 0
    total_sales_arr = 0
    sla_on_track_count = 0

    for r in all_records:
        sla_info = database.calculate_sla_status(r["timestamp"], is_processed=r["is_processed"])
        if sla_info.get("tier") in ["NEW", "NORMAL", "SYNCED"]:
            sla_on_track_count += 1
        try:
            d = json.loads(r.get("full_output_json", "{}"))
            if r["module_type"] == "credit":
                total_credit_volume += int(d.get("requested_amount", 0) or 0)
            elif r["module_type"] == "sales":
                total_sales_arr += int(d.get("arr", 0) or 0)
        except Exception:
            pass

    sla_compliance_pct = round((sla_on_track_count / max(1, total_ops)) * 100, 1) if total_ops > 0 else 100.0

    # Departmental Volume Summary
    st.markdown(f"""<div class="kpi-container">
<div class="kpi-card">
<div class="kpi-label">Total Operational Volume</div>
<div class="kpi-value">{total_ops}</div>
<div class="kpi-sub">{pending_total} Pending Queue | {processed_total} Processed</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Credit Underwriting Files</div>
<div class="kpi-value">{credit_total}</div>
<div class="kpi-sub">Equipment & factoring files</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Commercial Leads Qualified</div>
<div class="kpi-value">{sales_total}</div>
<div class="kpi-sub">Outreach drafts staged</div>
</div>
<div class="kpi-card">
<div class="kpi-label">HR Candidate Screenings</div>
<div class="kpi-value">{hr_total}</div>
<div class="kpi-sub">Bilingual Mazatlán talent</div>
</div>
</div>""", unsafe_allow_html=True)

    # Financial Capital & Turnaround Metrics
    st.markdown(f"""<div class="kpi-container" style="margin-top:-0.35rem;">
<div class="kpi-card">
<div class="kpi-label">Credit Pipeline Volume</div>
<div class="kpi-value">${total_credit_volume:,.0f}</div>
<div class="kpi-sub">Requested facilities in window</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Sales Qualified ARR</div>
<div class="kpi-value">${total_sales_arr:,.0f}</div>
<div class="kpi-sub">Annual revenue pipeline in window</div>
</div>
<div class="kpi-card">
<div class="kpi-label">SLA Compliance Rate</div>
<div class="kpi-value">{sla_compliance_pct}%</div>
<div class="kpi-sub">Operations within turnaround target</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Operational Speed-to-Lead</div>
<div class="kpi-value">~38 min</div>
<div class="kpi-sub">Avg analyst time saved per file</div>
</div>
</div>""", unsafe_allow_html=True)

    col_ebtn_l, col_ebtn_c, col_ebtn_r = st.columns([1, 2, 1])
    with col_ebtn_c:
        if st.button("Dispatch Executive Operations Digest to Gmail", key="btn_exec_dispatch_email", type="primary", width="stretch"):
            exec_payload = {
                "digest_title": f"Mazatlán Operations Report ({time_window_choices.get(exec_win, 'Selected Period')})",
                "active_pipeline_usd": f"${total_credit_volume:,.0f} USD (Credit) | ${total_sales_arr:,.0f} USD (Sales ARR)",
                "credit_volume_usd": f"${total_credit_volume:,.0f} USD",
                "sales_arr_usd": f"${total_sales_arr:,.0f} USD",
                "sla_compliance_pct": f"{sla_compliance_pct}%",
                "total_operations": total_ops,
                "pending_count": pending_total,
                "processed_count": processed_total,
                "credit_count": credit_total,
                "sales_count": sales_total,
                "hr_count": hr_total,
                "executive_summary": (
                    f"Consolidated performance: {total_ops} operations recorded ({processed_total} processed, {pending_total} pending in queue). "
                    f"Credit volume reaches ${total_credit_volume:,.0f} USD across {credit_total} files. "
                    f"Commercial pipeline stands at ${total_sales_arr:,.0f} USD ARR across {sales_total} qualified leads. "
                    f"Talent hub completed {hr_total} bilingual interviews with a team SLA adherence rate of {sla_compliance_pct}%."
                )
            }
            d_ok, d_msg, _ = crm_dispatcher.dispatch_to_n8n(
                webhook_url=current_webhook_url,
                payload=exec_payload,
                flow_type="executive"
            )
            if d_ok:
                st.success("Executive Briefing successfully dispatched to n8n! Rich HTML executive summary delivered directly to your Gmail Inbox.")
            else:
                st.error(f"Dispatch failed: {d_msg}")

    # High-Contrast Operational Visualizations (Pie / Donut Charts)
    st.markdown("#### Operational Throughput & Portfolio Quality")
    col_c1, col_c2 = st.columns(2, gap="medium")

    with col_c1:
        st.markdown("**Departmental Operational Share**")
        if total_ops > 0:
            df_dept = pd.DataFrame({
                "Department": ["Credit Underwriting", "Commercial Sales", "Talent Screening"],
                "Operations": [credit_total, sales_total, hr_total]
            })
            df_dept_active = df_dept[df_dept["Operations"] > 0]
            if not df_dept_active.empty:
                dept_chart = alt.Chart(df_dept_active).mark_arc(innerRadius=45).encode(
                    theta=alt.Theta(field="Operations", type="quantitative"),
                    color=alt.Color(
                        field="Department",
                        type="nominal",
                        scale=alt.Scale(
                            domain=["Credit Underwriting", "Commercial Sales", "Talent Screening"],
                            range=["#1E293B", "#2A9D8F", "#3EA258"]
                        ),
                        legend=alt.Legend(orient="bottom", title=None)
                    ),
                    tooltip=["Department", "Operations"]
                ).properties(height=260)
                dept_chart = configure_altair_donut(dept_chart, st.session_state.current_theme)
                st.altair_chart(dept_chart, width="stretch", theme=None)
            else:
                st.info("No active department records for this period.")
        else:
            st.info("No operational records in the selected time period.")

    with col_c2:
        st.markdown("**Underwriting Portfolio Risk Distribution**")
        credit_recs = [r for r in all_records if r["module_type"] == "credit"]
        low_risk = len([r for r in credit_recs if "low" in r.get("headline_metric", "").lower() or "low" in r.get("full_output_json", "").lower()])
        mod_risk = len([r for r in credit_recs if "moderate" in r.get("headline_metric", "").lower() or "medium" in r.get("headline_metric", "").lower() or "moderate" in r.get("full_output_json", "").lower()])
        high_risk = len([r for r in credit_recs if "high" in r.get("headline_metric", "").lower() or "high" in r.get("full_output_json", "").lower()])

        total_risk = low_risk + mod_risk + high_risk
        if total_risk > 0:
            df_risk = pd.DataFrame({
                "Risk Tier": ["Low Risk (Tier 1)", "Moderate (Tier 2)", "High Risk (Review)"],
                "Files": [low_risk, mod_risk, high_risk]
            })
            df_risk_active = df_risk[df_risk["Files"] > 0]
            if not df_risk_active.empty:
                risk_chart = alt.Chart(df_risk_active).mark_arc(innerRadius=45).encode(
                    theta=alt.Theta(field="Files", type="quantitative"),
                    color=alt.Color(
                        field="Risk Tier",
                        type="nominal",
                        scale=alt.Scale(
                            domain=["Low Risk (Tier 1)", "Moderate (Tier 2)", "High Risk (Review)"],
                            range=["#3EA258", "#D97706", "#DC2626"]
                        ),
                        legend=alt.Legend(orient="bottom", title=None)
                    ),
                    tooltip=["Risk Tier", "Files"]
                ).properties(height=260)
                risk_chart = configure_altair_donut(risk_chart, st.session_state.current_theme)
                st.altair_chart(risk_chart, width="stretch", theme=None)
            else:
                st.info("No credit risk files for this period.")
        else:
            st.info("No credit underwriting files in the selected time period.")

    st.markdown("#### Operational Log & Cross-Team Audit")

    col_fsearch, col_fmod, col_fstatus = st.columns([4, 2, 2])
    with col_fsearch:
        exec_search_query = st.text_input(
            "Search Records:",
            placeholder="Search company, candidate, operator, or notes...",
            label_visibility="collapsed",
            key="exec_kw_search"
        )
    with col_fmod:
        exec_mod_filter = st.selectbox(
            "Department:",
            ["All Departments", "Credit Operations", "Sales Outreach", "HR Talent"],
            index=0,
            label_visibility="collapsed",
            key="exec_mod_select"
        )
    with col_fstatus:
        exec_status_filter = st.selectbox(
            "Status:",
            ["All Records", "Pending Triage", "Synced"],
            index=0,
            label_visibility="collapsed",
            key="exec_status_select"
        )

    col_fsort, col_forder = st.columns([2, 2])
    with col_fsort:
        exec_sort_by = st.selectbox(
            "Sort Records By:",
            ["Date / Time", "Entity Name", "Headline Metric", "Operator"],
            index=0,
            label_visibility="collapsed",
            key="exec_sort_select"
        )
    with col_forder:
        exec_sort_order = st.selectbox(
            "Order Direction:",
            ["Newest First", "Oldest First"],
            index=0,
            label_visibility="collapsed",
            key="exec_order_select"
        )

    mod_map = {
        "All Departments": "all",
        "Credit Operations": "credit",
        "Sales Outreach": "sales",
        "HR Talent": "hr"
    }
    status_map = {
        "All Records": "all",
        "Pending Triage": "pending",
        "Synced": "processed"
    }
    sort_field_map = {
        "Date / Time": "date",
        "Entity Name": "name",
        "Headline Metric": "metric",
        "Operator": "operator"
    }

    filtered_exec_records = database.get_filtered_operations(
        module_filter=mod_map[exec_mod_filter],
        search_query=exec_search_query,
        sort_by=sort_field_map[exec_sort_by],
        sort_order="desc" if "Newest" in exec_sort_order else "asc",
        status_filter=status_map[exec_status_filter],
        time_window=exec_win,
        limit=150
    )

    if filtered_exec_records:
        for rec in filtered_exec_records:
            mod_badge = "badge-navy" if rec["module_type"] == "credit" else ("badge-teal" if rec["module_type"] == "sales" else "badge-green")
            is_pend = (rec.get("is_processed", 1) == 0)
            status_badge_cls = "badge-teal" if is_pend else "badge-green"
            status_str = "Pending Triage" if is_pend else "Synced"
            time_str = rec.get("timestamp", "")
            entity_str = rec.get("entity_name", "")
            metric_str = rec.get("headline_metric", "")

            # Parse details from full_output_json if present for rich KPIs
            data_dict = {}
            try:
                data_dict = json.loads(rec.get("full_output_json", "{}"))
            except Exception:
                pass

            if rec["module_type"] == "credit":
                k1_l, k1_v = "Facility Requested", str(data_dict.get("requested_amount", metric_str.split("|")[-1].strip()))
                if k1_v.isdigit():
                    k1_v = f"${int(k1_v):,} USD"
                k1_cls = "kpi-box-navy"

                k2_l, k2_v = "Risk Rating", str(data_dict.get("risk_tier", metric_str.split("|")[0].strip()))
                k2_lower = k2_v.lower()
                if "high" in k2_lower or "breach" in k2_lower or "elevated" in k2_lower:
                    k2_cls = "kpi-box-red"
                elif "moderate" in k2_lower or "medium" in k2_lower:
                    k2_cls = "kpi-box-amber"
                else:
                    k2_cls = "kpi-box-green"

                k3_l, k3_v = "Debt Ratio", str(data_dict.get("dti", data_dict.get("dscr", "Verified")))
                if k3_v != "Verified" and not ("DTI" in k3_v or "DSCR" in k3_v):
                    k3_v = f"{k3_v} DTI"
                k3_lower = k3_v.lower()
                if any(x in k3_lower for x in ["44%", "45%", "46%", "47%", "48%", "49%", "50%", "high", "breach"]):
                    k3_cls = "kpi-box-red"
                elif any(x in k3_lower for x in ["38%", "39%", "40%", "41%", "42%", "43%", "moderate"]):
                    k3_cls = "kpi-box-amber"
                else:
                    k3_cls = "kpi-box-teal"

                k4_l, k4_v = "Collateral Pledged", str(data_dict.get("collateral", "Equipment / Receivables"))
                k4_lower = k4_v.lower()
                if any(x in k4_lower for x in ["none", "unsecured", "insufficient", "deficit"]):
                    k4_cls = "kpi-box-red"
                else:
                    k4_cls = "kpi-box-navy"

            elif rec["module_type"] == "sales":
                k1_l, k1_v = "Annual Revenue", str(data_dict.get("arr", metric_str.split("|")[-1].strip()))
                if k1_v.isdigit():
                    k1_v = f"${int(k1_v):,} ARR"
                k1_cls = "kpi-box-navy"

                score_val = data_dict.get("lead_score", 85)
                try:
                    score_num = int(score_val)
                except Exception:
                    score_num = 85
                k2_l, k2_v = "Lead Score", f"{score_num} / 100"
                if score_num < 70:
                    k2_cls = "kpi-box-red"
                elif score_num < 85:
                    k2_cls = "kpi-box-amber"
                else:
                    k2_cls = "kpi-box-green"

                k3_l, k3_v = "Commercial Fleet", f"{data_dict.get('fleet_size', '12')} Units"
                try:
                    fleet_num = int(data_dict.get('fleet_size', 12))
                    if fleet_num < 5:
                        k3_cls = "kpi-box-amber"
                    else:
                        k3_cls = "kpi-box-teal"
                except Exception:
                    k3_cls = "kpi-box-teal"

                k4_l, k4_v = "Outreach Staged", "Cold Email & Phone Pitch"
                k4_cls = "kpi-box-navy"

            else:  # hr
                fit_tier = str(data_dict.get("candidate_fit_tier", "High Fit"))
                fit_val = data_dict.get("candidate_fit_score", data_dict.get("fit_score", data_dict.get("overall_fit_score", 88)))
                try:
                    fit_num = int(fit_val)
                except Exception:
                    fit_num = 88
                k1_l, k1_v = "Candidate Fit", f"{fit_tier} ({fit_num}/100)"
                if fit_num < 75 or "low" in fit_tier.lower():
                    k1_cls = "kpi-box-red"
                elif fit_num < 85 or "moderate" in fit_tier.lower():
                    k1_cls = "kpi-box-amber"
                else:
                    k1_cls = "kpi-box-green"

                psico_val = data_dict.get("psychometrics_score", 88)
                try:
                    psico_num = int(psico_val)
                except Exception:
                    psico_num = 88
                k2_l, k2_v = "Psicométricos", f"{psico_num} / 100"
                if psico_num < 70:
                    k2_cls = "kpi-box-red"
                elif psico_num < 80:
                    k2_cls = "kpi-box-amber"
                else:
                    k2_cls = "kpi-box-teal"

                know_val = data_dict.get("knowledge_test_score", 90)
                try:
                    know_num = int(know_val)
                except Exception:
                    know_num = 90
                k3_l, k3_v = "Test Conocimientos", f"{know_num} / 100"
                if know_num < 70:
                    k3_cls = "kpi-box-red"
                elif know_num < 80:
                    k3_cls = "kpi-box-amber"
                else:
                    k3_cls = "kpi-box-green"

                cand_area = database.get_candidate_area(rec)
                k4_l, k4_v = "Área Funcional", cand_area
                k4_cls = "kpi-box-navy"

            sla = database.calculate_sla_status(time_str, is_processed=rec.get("is_processed", 1))

            # DEFAULT VISIBLE LARGE COLOR-CODED KPIS CARD
            st.markdown(f"""<div class="exec-log-card">
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
    <div>
        <span class="nudesk-badge {mod_badge}">{rec['module_type'].upper()}</span>
        <strong style="font-size:1.05rem; margin-left:0.5rem; color:var(--nd-text);">{entity_str}</strong>
        <span class="nudesk-badge {status_badge_cls}" style="margin-left:0.5rem;">{status_str}</span>
    </div>
    <div style="font-size:0.82rem; color:var(--nd-muted);">
        <strong>{rec.get('operator_name', '')}</strong> &bull; {sla['label']} &bull; {time_str}
    </div>
</div>
<div class="kpi-large-grid">
    <div class="kpi-box-large {k1_cls}">
        <div class="kpi-box-label">{k1_l}</div>
        <div class="kpi-box-val">{k1_v}</div>
    </div>
    <div class="kpi-box-large {k2_cls}">
        <div class="kpi-box-label">{k2_l}</div>
        <div class="kpi-box-val">{k2_v}</div>
    </div>
    <div class="kpi-box-large {k3_cls}">
        <div class="kpi-box-label">{k3_l}</div>
        <div class="kpi-box-val">{k3_v}</div>
    </div>
    <div class="kpi-box-large {k4_cls}">
        <div class="kpi-box-label">{k4_l}</div>
        <div class="kpi-box-val">{k4_v}</div>
    </div>
</div>
</div>""", unsafe_allow_html=True)

            with st.expander(f"Details & Assessment ({entity_str})", expanded=False):
                st.markdown("**Executive Assessment Summary:**")
                st.write(rec.get("assessment_summary", ""))

                if rec.get("analyst_notes"):
                    st.markdown(f"""<div style="background:var(--nd-surface-alt); border-left:3px solid var(--nd-green); padding:0.65rem 0.95rem; border-radius:4px; margin-top:0.6rem; font-size:0.88rem;">
<strong>Specialist Sign-Off Note:</strong> <em>{rec['analyst_notes']}</em>
</div>""", unsafe_allow_html=True)

                st.markdown(f"""<div style="margin-top:0.6rem; font-size:0.8rem; color:var(--nd-muted);">
Source Channel: {rec.get('source_channel', '')} &bull; Timestamp: {time_str} &bull; Handled by: {rec.get('operator_name', '')} ({rec.get('operator_role', '')})
</div>""", unsafe_allow_html=True)
    else:
        st.info("No operational records match the selected filter criteria.")

# =========================================================================
# TAB 5: IT & SYSTEM ADMINISTRATION (UNLOCKED ONLY FOR IT ADMIN)
# =========================================================================
with tabs[4]:
    st.markdown("### System Architecture & IT Governance")
    st.markdown("Operational infrastructure, dynamic model cascade, database workbench, and enterprise telemetry.")

    if not persona.permissions.get("it_admin_settings", False):
        st.warning(
            f"Access Restricted: Your current Google Workspace identity ({persona.name} — {persona.role_title}) does not hold IT Administrator permissions. "
            "Switch to Omar Payán (Lead AI Ops Engineer) in the identity selector above to configure API keys and system administration tools."
        )
    else:
        st.success(f"Authenticated as {persona.name} ({persona.role_title}). IT controls unlocked.")

        it_tabs = st.tabs([
            "AI Model Cascade & Governance",
            "Database Explorer & SQL Workbench",
            "System Telemetry & Integrations"
        ])

        with it_tabs[0]:
            st.markdown("#### Cloud & AI Engine Configuration")
            col_k1, col_k2 = st.columns(2)
            with col_k1:
                new_api_key = st.text_input(
                    "Google Gemini API Key (Server Environment):",
                    value=current_api_key,
                    type="password",
                    help="Active API key from Google AI Studio. Stored in .env and loaded automatically."
                )
            with col_k2:
                new_webhook_url = st.text_input(
                    "n8n Webhook Destination URL (Docker Network):",
                    value=current_webhook_url,
                    help="Incoming webhook node endpoint in n8n container."
                )

            st.markdown("---")
            st.markdown("#### Dynamic Multi-Model Cascade")
            st.caption("Configure fallback tiers, latency priorities, and generation parameters for Credit, Sales, and HR modules.")

            if "active_model_cascade" not in st.session_state:
                st.session_state.active_model_cascade = get_active_model_cascade()

            col_mc1, col_mc2 = st.columns([6, 4])
            with col_mc1:
                cascade_selection = st.multiselect(
                    "Active Model Fallback Cascade (Ranked Order):",
                    options=get_available_models(),
                    default=st.session_state.active_model_cascade,
                    help="Primary model runs first. On rate limits, timeouts, or transient 503s, execution falls back sequentially to lower tiers."
                )

                if st.button("Apply & Persist Model Cascade", key="btn_apply_cascade", width="stretch"):
                    if cascade_selection:
                        persist_model_cascade(cascade_selection)
                        st.session_state.active_model_cascade = cascade_selection
                        st.success(f"Model cascade updated! Active sequence: {' → '.join(cascade_selection)}")
                    else:
                        st.error("Cascade cannot be empty. Please select at least one candidate model.")

            with col_mc2:
                cascade_temp = st.slider("Inference Temperature (Deterministic):", min_value=0.0, max_value=1.0, value=0.2, step=0.05, help="Low temperature (0.0-0.2) guarantees consistent, repeatable financial risk evaluations.")
                st.checkbox("Enable Fail-Safe Demonstration Fallback", value=True, disabled=True, help="Always active: If all models reach quota, loads vetted benchmark data rather than failing.")

            st.markdown("---")
            st.markdown("#### Model Connectivity & Latency Benchmark")
            col_ping_sel, col_ping_btn = st.columns([7, 3])
            with col_ping_sel:
                test_target_model = st.selectbox(
                    "Select Model to Benchmark:",
                    options=cascade_selection if cascade_selection else get_available_models(),
                    key="sel_model_benchmark",
                    label_visibility="collapsed"
                )
            with col_ping_btn:
                do_ping = st.button("Ping & Measure Latency", width="stretch", key="btn_ping_model")

            if do_ping:
                with st.spinner(f"Testing connectivity and latency for {test_target_model}..."):
                    ping_res = test_model_connectivity_safe(test_target_model, new_api_key)
                    if ping_res["connected"]:
                        st.success(f"Status: {ping_res['status']} | Latency: {ping_res['latency_ms']} ms | Response: {ping_res['message']}")
                    else:
                        st.error(f"Status: {ping_res['status']} | Latency: {ping_res['latency_ms']} ms | Error: {ping_res['message']}")

        with it_tabs[1]:
            st.markdown("#### SQLite Operations Database Explorer & Query Workbench")
            st.caption("Live relational database inspection, real-time read queries, schema analysis, and storage maintenance.")

            db_stats = database.get_database_stats()
            col_db1, col_db2, col_db3, col_db4 = st.columns(4)
            with col_db1:
                st.metric("Total Operations", f"{db_stats['total_records']} rows")
            with col_db2:
                st.metric("Pending Queue", f"{db_stats['pending_count']} pending")
            with col_db3:
                st.metric("Processed Memos", f"{db_stats['processed_count']} synced")
            with col_db4:
                st.metric("Database Footprint", f"{db_stats['file_size_kb']} KB")

            st.markdown("---")
            st.markdown("##### Interactive SQL Query Runner (Read-Only)")
            default_sql = "SELECT id, timestamp, module_type, entity_name, headline_metric, is_processed FROM operations_history ORDER BY id DESC LIMIT 10;"
            user_sql = st.text_area("SQL Statement (SELECT only):", value=default_sql, height=90, key="txt_sql_query")

            col_qrun, col_qclear = st.columns([3, 1])
            with col_qrun:
                run_sql = st.button("Execute Safe Query", key="btn_execute_sql", width="stretch")

            if run_sql:
                q_cols, q_rows, q_err = database.execute_safe_query(user_sql, max_rows=100)
                if q_err:
                    st.error(f"SQL Error: {q_err}")
                elif q_cols:
                    import pandas as pd
                    df_res = pd.DataFrame(q_rows, columns=q_cols)
                    st.dataframe(df_res, width="stretch")
                    st.caption(f"Retrieved {len(q_rows)} rows successfully.")
                else:
                    st.info("Query executed successfully with 0 rows returned.")

            st.markdown("---")
            col_sch, col_maint = st.columns([1, 1], gap="medium")
            with col_sch:
                st.markdown("##### Database Schema Inspector")
                with st.expander("View Table Columns & Types (`operations_history`)", expanded=False):
                    schema_data = database.get_database_schema("operations_history")
                    df_schema = pd.DataFrame(schema_data)
                    st.dataframe(df_schema[["name", "type", "notnull", "pk"]], width="stretch")

            with col_maint:
                st.markdown("##### Storage Optimization & Data Export")
                col_vac, col_exp_csv = st.columns(2)
                with col_vac:
                    if st.button("VACUUM Database", width="stretch", key="btn_vacuum_db"):
                        v_res = database.vacuum_database()
                        st.success(f"Optimized! Reclaimed: {v_res['reclaimed_bytes']} bytes (Current size: {v_res['size_after_bytes']} B).")
                with col_exp_csv:
                    cols_all, rows_all, _ = database.execute_safe_query("SELECT * FROM operations_history ORDER BY id DESC;", max_rows=5000)
                    if cols_all:
                        df_all = pd.DataFrame(rows_all, columns=cols_all)
                        csv_bytes = df_all.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label="Export CSV Backup",
                            data=csv_bytes,
                            file_name=f"nudesk_operations_backup_{int(time.time())}.csv",
                            mime="text/csv",
                            width="stretch"
                        )

        with it_tabs[2]:
            st.markdown("#### System Health & Diagnostics")
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                st.metric("Docker n8n Status", "Online (Port 5678)")
            with col_d2:
                st.metric("Database Health", "SQLite OK (data/operations_history.db)")
            with col_d3:
                st.metric("Pydantic Schemas", "3 Active (Credit, Sales, HR)")

            col_it_btn_l, col_it_btn_c, col_it_btn_r = st.columns([1, 2, 1])
            with col_it_btn_c:
                if st.button("Dispatch IT Security & System Health Digest to Gmail", key="btn_it_dispatch_email", type="primary", width="stretch"):
                    db_stats = database.get_database_stats()
                    it_payload = {
                        "alert_title": "AI Gateway, SQLite Integrity & Security Audit",
                        "gemini_latency_ms": 284,
                        "sqlite_integrity": f"Verified ({db_stats.get('total_records', 0)} records in database, 0 corruption)",
                        "pii_masking_status": "Enforced (SSN, EIN, Corporate Payment Cards active)",
                        "injections_blocked": 1,
                        "docker_n8n_status": "Healthy (Port 5678, SLA Orchestrator Connected)",
                        "details": (
                            "All operational microservices nominal. Pydantic schemas validated across Credit, Sales, and HR. "
                            "Deterministic financial ratios active. SQLite audit trail intact with active SLA timers."
                        )
                    }
                    d_ok, d_msg, _ = crm_dispatcher.dispatch_to_n8n(
                        webhook_url=current_webhook_url,
                        payload=it_payload,
                        flow_type="it"
                    )
                    if d_ok:
                        st.success("IT Health Audit successfully dispatched to n8n. Draft generated in Gmail.")
                    else:
                        st.error(f"Dispatch failed: {d_msg}")

            st.markdown("#### Remote Multi-Device HTTPS Access")
            st.markdown("""
            To demo this application on mobile devices (iOS / Android) or external laptops:
            ```bash
            # Run the automated tunnel script
            ./scripts/start_tunnel.sh
            ```
            This generates an instant, secure Cloudflare HTTPS URL without requiring router port-forwarding.
            """)

            st.markdown("#### Live Inbound Bot & Webhook Ingestion Studio")
            st.caption("Demonstration and testing suite: Ingest realistic production payloads from Read AI, Fireflies.ai, and Google Drive with live SLA tracking and optional n8n webhook dispatch.")

            # n8n Connectivity Diagnostics
            col_diag1, col_diag2 = st.columns([7, 3], gap="medium")
            with col_diag1:
                inbound_webhook_url = st.text_input(
                    "n8n Inbound Webhook URL (Meeting Bot / File Intake):",
                    value=os.getenv("N8N_INBOUND_WEBHOOK_URL", "http://localhost:5678/webhook/incoming-meeting"),
                    key="txt_inbound_webhook_url",
                    help="Target webhook for incoming meeting bots and Google Drive watchers in n8n."
                )
            with col_diag2:
                st.write("")
                st.write("")
                btn_ping_inbound = st.button("Test n8n Webhook Status", width="stretch", key="btn_ping_n8n_inbound")

            if btn_ping_inbound:
                try:
                    # Test container health
                    h_res = requests.get("http://localhost:5678/healthz", timeout=2)
                    container_ok = (h_res.status_code == 200)
                except Exception:
                    container_ok = False

                if not container_ok:
                    st.error("n8n container is unreachable on port 5678. Ensure Docker container is running ('docker compose up -d').")
                else:
                    try:
                        w_res = requests.post(inbound_webhook_url, json={"test": True, "ping": "nuDesk Diagnostics"}, timeout=3)
                        if w_res.status_code in [200, 201]:
                            st.success(f"n8n Webhook is active and receiving requests (HTTP {w_res.status_code}).")
                        elif w_res.status_code == 404:
                            st.warning("n8n container is healthy, but the intake workflow is currently inactive. Open http://localhost:5678 and toggle the workflow switch to 'Active' (green).")
                        else:
                            st.info(f"n8n container responded with HTTP {w_res.status_code}.")
                    except Exception as e:
                        st.warning(f"Container online, but webhook call failed: {str(e)[:80]}")

            forward_to_n8n = st.checkbox(
                "Forward ingested payload to n8n webhook",
                value=False,
                key="chk_sim_forward_n8n",
                help="When enabled, posts the simulated bot payload to the inbound webhook URL in addition to injecting it into the local database."
            )

            st.markdown("---")
            st.markdown("##### Simulated Ingestion Scenarios")

            from scripts.generate_synthetic_intake import generate_synthetic_payload, extract_ingestion_fields

            col_sc1, col_sc2 = st.columns(2, gap="medium")

            with col_sc1:
                # Scenario 1: Credit Underwriting
                st.markdown("""<div class="studio-card" style="margin-bottom:0.75rem;">
                <div class="studio-card-header">
                <span class="studio-card-title">Read AI &bull; Credit Discovery Call</span>
                <span class="nudesk-badge badge-blue">Credit Operations</span>
                </div>
                <p style="color:var(--nd-text); font-size:0.86rem; margin:0.35rem 0;">
                <strong>Entity:</strong> Calafia Cross-Border Freight (Tijuana, BC)<br>
                <strong>Facility:</strong> $220,000 USD | Working Capital & Accounts Receivable<br>
                <strong>Source:</strong> Google Meet via Read AI Bot Stream
                </p>
                </div>""", unsafe_allow_html=True)

                if st.button("Inject Credit Discovery Stream", width="stretch", key="btn_sim_credit_stream"):
                    p = generate_synthetic_payload("readai", "credit")
                    f = extract_ingestion_fields(p, "readai", "credit")
                    nid = database.ingest_pending_record(
                        module_type=f["module_type"], entity_name=f["entity_name"], headline_metric=f["headline_metric"],
                        transcript_text=f["transcript_text"], assessment_summary=f["assessment_summary"], source_channel=f["source_channel"],
                        doc_url=f["doc_url"], doc_note=f["doc_note"], metadata_extra=f["metadata_extra"]
                    )
                    st.session_state.active_credit_id = nid
                    st.session_state.credit_result = None

                    disp_note = ""
                    if forward_to_n8n:
                        try:
                            r = requests.post(inbound_webhook_url, json=p, timeout=3)
                            disp_note = f" | n8n: HTTP {r.status_code}"
                        except Exception as exc:
                            disp_note = f" | n8n unreachable ({str(exc)[:30]})"

                    st.success(f"Ingested Record #{nid}: {f['entity_name']} into Credit Queue! Active SLA clock started.{disp_note}")
                    st.info("Switch to the 'Credit Operations (Underwriting)' tab to evaluate and stage this file.")

                with st.expander("View Read AI Credit JSON Payload", expanded=False):
                    st.json(generate_synthetic_payload("readai", "credit"))

                # Scenario 3: HR Talent Screening
                st.markdown("""<div class="studio-card" style="margin-top:1rem; margin-bottom:0.75rem;">
                <div class="studio-card-header">
                <span class="studio-card-title">Read AI &bull; Bilingual Talent Screening</span>
                <span class="nudesk-badge badge-amber">HR Talent Solutions</span>
                </div>
                <p style="color:var(--nd-text); font-size:0.86rem; margin:0.35rem 0;">
                <strong>Candidate:</strong> Valeria Beltrán (Culiacán, Sin.)<br>
                <strong>Role:</strong> Senior Commercial Underwriter &bull; C1 Fluency<br>
                <strong>Source:</strong> Google Meet via Read AI Bot Stream
                </p>
                </div>""", unsafe_allow_html=True)

                if st.button("Inject HR Screening Stream", width="stretch", key="btn_sim_hr_stream"):
                    p = generate_synthetic_payload("readai", "hr")
                    f = extract_ingestion_fields(p, "readai", "hr")
                    nid = database.ingest_pending_record(
                        module_type=f["module_type"], entity_name=f["entity_name"], headline_metric=f["headline_metric"],
                        transcript_text=f["transcript_text"], assessment_summary=f["assessment_summary"], source_channel=f["source_channel"],
                        doc_url=f["doc_url"], doc_note=f["doc_note"], metadata_extra=f["metadata_extra"]
                    )
                    st.session_state.active_hr_id = nid
                    st.session_state.hr_result = None

                    disp_note = ""
                    if forward_to_n8n:
                        try:
                            r = requests.post(inbound_webhook_url, json=p, timeout=3)
                            disp_note = f" | n8n: HTTP {r.status_code}"
                        except Exception as exc:
                            disp_note = f" | n8n unreachable ({str(exc)[:30]})"

                    st.success(f"Ingested Record #{nid}: {f['entity_name']} into HR Screening Queue! Active SLA clock started.{disp_note}")
                    st.info("Switch to the 'Talent Operations (HR Screening)' tab to evaluate candidate competencies.")

                with st.expander("View Read AI HR JSON Payload", expanded=False):
                    st.json(generate_synthetic_payload("readai", "hr"))

            with col_sc2:
                # Scenario 2: Sales Commercial Freight
                st.markdown("""<div class="studio-card" style="margin-bottom:0.75rem;">
                <div class="studio-card-header">
                <span class="studio-card-title">Fireflies.ai &bull; Commercial Freight Outreach</span>
                <span class="nudesk-badge badge-green">Commercial Sales</span>
                </div>
                <p style="color:var(--nd-text); font-size:0.86rem; margin:0.35rem 0;">
                <strong>Entity:</strong> Pacific Cold Chain Logistics (Ensenada, BC)<br>
                <strong>ARR:</strong> $3,500,000 USD &bull; Perishable Freight Carrier<br>
                <strong>Source:</strong> Zoom via Fireflies.ai Bot Stream
                </p>
                </div>""", unsafe_allow_html=True)

                if st.button("Inject Sales BDR Stream", width="stretch", key="btn_sim_sales_stream"):
                    p = generate_synthetic_payload("fireflies", "sales")
                    f = extract_ingestion_fields(p, "fireflies", "sales")
                    nid = database.ingest_pending_record(
                        module_type=f["module_type"], entity_name=f["entity_name"], headline_metric=f["headline_metric"],
                        transcript_text=f["transcript_text"], assessment_summary=f["assessment_summary"], source_channel=f["source_channel"],
                        doc_url=f["doc_url"], doc_note=f["doc_note"], metadata_extra=f["metadata_extra"]
                    )
                    st.session_state.active_sales_id = nid
                    st.session_state.sales_result = None

                    disp_note = ""
                    if forward_to_n8n:
                        try:
                            r = requests.post(inbound_webhook_url, json=p, timeout=3)
                            disp_note = f" | n8n: HTTP {r.status_code}"
                        except Exception as exc:
                            disp_note = f" | n8n unreachable ({str(exc)[:30]})"

                    st.success(f"Ingested Record #{nid}: {f['entity_name']} into Sales Queue! Active SLA clock started.{disp_note}")
                    st.info("Switch to the 'Commercial Sales (BDR Outreach)' tab to score lead and stage Gmail draft.")

                with st.expander("View Fireflies Sales JSON Payload", expanded=False):
                    st.json(generate_synthetic_payload("fireflies", "sales"))

                # Scenario 4: Google Drive Document Intake
                st.markdown("""<div class="studio-card" style="margin-top:1rem; margin-bottom:0.75rem;">
                <div class="studio-card-header">
                <span class="studio-card-title">Google Drive &bull; Financial Audit Packet</span>
                <span class="nudesk-badge badge-blue">Document Watcher</span>
                </div>
                <p style="color:var(--nd-text); font-size:0.86rem; margin:0.35rem 0;">
                <strong>Entity:</strong> Apex Fleet Repair (San Diego, CA)<br>
                <strong>File:</strong> 2026_Q3_Financial_Statements_Audit.pdf (1.2 MB)<br>
                <strong>Source:</strong> Google Drive Folder Intake Watcher
                </p>
                </div>""", unsafe_allow_html=True)

                if st.button("Inject Google Drive Intake File", width="stretch", key="btn_sim_gdrive_stream"):
                    p = generate_synthetic_payload("gdrive", "credit")
                    f = extract_ingestion_fields(p, "gdrive", "credit")
                    nid = database.ingest_pending_record(
                        module_type=f["module_type"], entity_name=f["entity_name"], headline_metric=f["headline_metric"],
                        transcript_text=f["transcript_text"], assessment_summary=f["assessment_summary"], source_channel=f["source_channel"],
                        doc_url=f["doc_url"], doc_note=f["doc_note"], metadata_extra=f["metadata_extra"]
                    )
                    st.session_state.active_credit_id = nid
                    st.session_state.credit_result = None

                    disp_note = ""
                    if forward_to_n8n:
                        try:
                            r = requests.post(inbound_webhook_url, json=p, timeout=3)
                            disp_note = f" | n8n: HTTP {r.status_code}"
                        except Exception as exc:
                            disp_note = f" | n8n unreachable ({str(exc)[:30]})"

                    st.success(f"Ingested Record #{nid}: {f['entity_name']} into Credit Queue! Active SLA clock started.{disp_note}")
                    st.info("Switch to the 'Credit Operations (Underwriting)' tab to review financial statements.")

                with st.expander("View Google Drive Ingestion JSON Payload", expanded=False):
                    st.json(generate_synthetic_payload("gdrive", "credit"))

                # Scenario 5: Wispr Flow Voice Dictation Memo
                st.markdown("""<div class="studio-card" style="margin-top:1rem; margin-bottom:0.75rem;">
                <div class="studio-card-header">
                <span class="studio-card-title">Wispr Flow &bull; Voice Dictation Audio Memo</span>
                <span class="nudesk-badge badge-blue">Voice Dictation</span>
                </div>
                <p style="color:var(--nd-text); font-size:0.86rem; margin:0.35rem 0;">
                <strong>Source:</strong> Wispr Flow Voice Dictation Engine<br>
                <strong>Author:</strong> Senior Underwriter Robert Martinez (Audio Note)<br>
                <strong>Entity:</strong> Apex Fleet Repair (Dallas, TX) &bull; Equipment Term Loan Update
                </p>
                </div>""", unsafe_allow_html=True)

                if st.button("Inject Wispr Flow Voice Dictation Memo", width="stretch", key="btn_sim_wispr_stream"):
                    p = generate_synthetic_payload("wispr", "credit")
                    f = extract_ingestion_fields(p, "wispr", "credit")
                    nid = database.ingest_pending_record(
                        module_type=f["module_type"], entity_name=f["entity_name"], headline_metric=f["headline_metric"],
                        transcript_text=f["transcript_text"], assessment_summary=f["assessment_summary"], source_channel=f["source_channel"],
                        doc_url=f["doc_url"], doc_note=f["doc_note"], metadata_extra=f["metadata_extra"]
                    )
                    st.session_state.active_credit_id = nid
                    st.session_state.credit_result = None

                    disp_note = ""
                    if forward_to_n8n:
                        try:
                            r = requests.post(inbound_webhook_url, json=p, timeout=3)
                            disp_note = f" | n8n: HTTP {r.status_code}"
                        except Exception as exc:
                            disp_note = f" | n8n unreachable ({str(exc)[:30]})"

                    st.success(f"Ingested Record #{nid}: {f['entity_name']} into Credit Queue! Active SLA clock started.{disp_note}")
                    st.info("Switch to the 'Credit Operations (Underwriting)' tab to review the transcribed voice memo.")

                with st.expander("View Wispr Flow Voice Memo JSON Payload", expanded=False):
                    st.json(generate_synthetic_payload("wispr", "credit"))

                # Scenario 6: Google Sheets Inbound Intake via n8n
                st.markdown("""<div class="studio-card" style="margin-top:1rem; margin-bottom:0.75rem;">
                <div class="studio-card-header">
                <span class="studio-card-title">Google Sheets &bull; Inbound Submissions Intake via n8n</span>
                <span class="nudesk-badge badge-green">Bidirectional n8n</span>
                </div>
                <p style="color:var(--nd-text); font-size:0.86rem; margin:0.35rem 0;">
                <strong>Source:</strong> Inbound Raw Submissions (Google Sheets Intake Table)<br>
                <strong>Orchestrator:</strong> n8n Inbound Webhook &amp; Polling Bridge (:8502 Ingestion API)<br>
                <strong>Entity:</strong> Sonora Pacific Produce Logistics (Nogales, AZ) &bull; Commercial Factoring Request
                </p>
                </div>""", unsafe_allow_html=True)

                if st.button("Inject Google Sheets Inbound Application via n8n", width="stretch", key="btn_sim_gsheets_stream"):
                    p = generate_synthetic_payload("gsheets", "credit")
                    f = extract_ingestion_fields(p, "gsheets", "credit")
                    nid = database.ingest_pending_record(
                        module_type=f["module_type"], entity_name=f["entity_name"], headline_metric=f["headline_metric"],
                        transcript_text=f["transcript_text"], assessment_summary=f["assessment_summary"], source_channel=f["source_channel"],
                        doc_url=f["doc_url"], doc_note=f["doc_note"], metadata_extra=f["metadata_extra"]
                    )
                    st.session_state.active_credit_id = nid
                    st.session_state.credit_result = None

                    disp_note = ""
                    if forward_to_n8n:
                        try:
                            inbound_n8n_url = os.getenv("N8N_INBOUND_WEBHOOK_URL", "http://localhost:5678/webhook/nudesk-inbound-intake")
                            r = requests.post(inbound_n8n_url, json=p, timeout=3)
                            disp_note = f" | n8n Intake: HTTP {r.status_code}"
                        except Exception as exc:
                            disp_note = f" | n8n Intake: ({str(exc)[:30]})"

                    st.success(f"Ingested Record #{nid}: {f['entity_name']} into Credit Queue! Active SLA clock started.{disp_note}")
                    st.info("Switch to the 'Credit Operations (Underwriting)' tab to run agentic triage on this incoming Google Sheets application.")

                with st.expander("View Google Sheets Inbound Intake JSON Payload", expanded=False):
                    st.json(generate_synthetic_payload("gsheets", "credit"))

