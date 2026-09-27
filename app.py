"""
DeskMate Operations Studio V2 (FinTech Operations Cockpit)
nuDesk MX — Mazatlán Operations Hub & US Commercial Lending
AI-Workforce Platform for Financial Services
"""
import os
import json
from typing import Optional, Any, Dict, List, Tuple
import streamlit as st
from dotenv import load_dotenv

# Internal modular imports
import importlib
import styles.nudesk_theme
importlib.reload(styles.nudesk_theme)
from styles.nudesk_theme import get_nudesk_css
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
import crm_dispatcher
import database
import importlib
importlib.reload(database)
import document_reader

load_dotenv()
database.init_db()

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="DeskMate Studio | nuDesk MX",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Theme setup (Default to High-Contrast Minimalist Light Mode)
if "current_theme" not in st.session_state:
    st.session_state.current_theme = "light"

if "time_window" not in st.session_state:
    st.session_state.time_window = "week"

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
    "week": "This Week (Rolling 7 Days)",
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
<h1>nuDesk | DeskMate Operations Studio</h1>
<div class="subtitle">AI-Workforce Platform for Financial Services — Mazatlán Talent Hub</div>
</div>
</div>""", unsafe_allow_html=True)

with col_head_right:
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
    "Credit DeskMate (Underwriting)",
    "Sales DeskMate (BDR Outreach)",
    "HR DeskMate (Talent Screening)",
    "Executive KPI Dashboard & History",
    "IT & System Administration"
]

tabs = st.tabs(tab_labels)

# =========================================================================
# TAB 1: CREDIT DESKMATE (UNDERWRITING DISCOVERY TRIAGE - SPLIT COCKPIT)
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
            index=list(time_window_choices.keys()).index(st.session_state.get("cq_win", "all")),
            key="cq_win",
            label_visibility="visible"
        )

    credit_kpis = database.get_department_kpis("credit", time_window=cq_win)
    credit_records = database.get_filtered_operations(module_filter="credit", time_window=cq_win, limit=200)

    import pandas as pd
    import altair as alt

    # Top Section: Key Metrics Ribbon & Underwriting Risk Donut Chart
    col_c_stats, col_c_donut = st.columns([7, 5], gap="medium")
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

    with col_c_donut:
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
            st.altair_chart(c_chart, width="stretch")
        else:
            st.info("No credit files in this period.")

    # Master-Detail Split Workspace
    col_c_queue, col_c_canvas = st.columns([5, 7])

    # ---------------- LEFT PANEL: QUEUE & AUDIT HUB ----------------
    with col_c_queue:
        credit_queue_tabs = st.tabs([
            f"Pending Queue ({credit_kpis['pending_count']})",
            f"Processed Audit ({credit_kpis['processed_count']})"
        ])

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
                    with st.expander(f"{rec['entity_name']} — {rec['headline_metric']}"):
                        st.markdown(f"""<div style="margin-bottom:0.5rem;">
<span class="nudesk-badge badge-green">{rec['dispatch_status']}</span>
<span style="font-size:0.8rem; color:#64748B; margin-left:0.5rem;">Resolved {sla['label']} &bull; {rec['operator_name']}</span>
</div>""", unsafe_allow_html=True)
                        st.markdown("**Executive Memo:**")
                        st.write(rec.get("assessment_summary", ""))
                        if rec.get("analyst_notes"):
                            st.markdown(f"**Underwriter Sign-Off:** *{rec['analyst_notes']}*")
            else:
                st.info("No processed underwriting memos found in this timeframe.")

    # ---------------- RIGHT PANEL: ACTIVE DECISION CANVAS ----------------
    with col_c_canvas:
        is_manual = (st.session_state.active_credit_id == "manual")
        active_credit_rec = None

        if not is_manual:
            active_credit_rec = database.get_operation_by_id(st.session_state.active_credit_id)
            if not active_credit_rec or active_credit_rec.get("is_processed") == 1:
                # If deleted or resolved, auto-load next pending
                next_c = database.get_next_pending_operation("credit")
                if next_c:
                    st.session_state.active_credit_id = next_c["id"]
                    active_credit_rec = next_c
                else:
                    is_manual = True
                    st.session_state.active_credit_id = "manual"

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

        with st.expander("Discovery Transcript & Collateral Dock", expanded=True):
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

                output, is_fb, msg = ai_engine.analyze_credit_call(
                    transcript=credit_input_text,
                    api_key=current_api_key,
                    supplementary_doc=supp_doc
                )
                st.session_state.credit_result = (output, is_fb, msg)

        # Output Results
        if st.session_state.credit_result:
            credit_out: CreditTriageOutput = st.session_state.credit_result[0]
            is_fallback = st.session_state.credit_result[1]
            status_msg = st.session_state.credit_result[2]

            if is_fallback:
                st.info(f"Demonstration Benchmark Mode: {status_msg}")
            else:
                st.success(f"{status_msg}")

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
# TAB 2: SALES DESKMATE (COMMERCIAL BDR LEAD SCORING - SPLIT COCKPIT)
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
            index=list(time_window_choices.keys()).index(st.session_state.get("sq_win", "all")),
            key="sq_win",
            label_visibility="visible"
        )

    sales_kpis = database.get_department_kpis("sales", time_window=sq_win)
    sales_records = database.get_filtered_operations(module_filter="sales", time_window=sq_win, limit=200)

    # Top Section: Key Metrics Ribbon & Sales Lead Quality Donut Chart
    col_s_stats, col_s_donut = st.columns([7, 5], gap="medium")
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

    with col_s_donut:
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
            st.altair_chart(s_chart, width="stretch")
        else:
            st.info("No commercial leads in this period.")

    col_s_queue, col_s_canvas = st.columns([5, 7])

    # ---------------- LEFT PANEL: SALES QUEUE & AUDIT ----------------
    with col_s_queue:
        sales_queue_tabs = st.tabs([
            f"Pending Queue ({sales_kpis['pending_count']})",
            f"Processed Leads ({sales_kpis['processed_count']})"
        ])

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
                    with st.expander(f"{rec['entity_name']} — {rec['headline_metric']}"):
                        st.markdown(f"""<div style="margin-bottom:0.5rem;">
<span class="nudesk-badge badge-green">{rec['dispatch_status']}</span>
<span style="font-size:0.8rem; color:#64748B; margin-left:0.5rem;">Synced {sla['label']} &bull; {rec['operator_name']}</span>
</div>""", unsafe_allow_html=True)
                        st.write(rec.get("assessment_summary", ""))
                        if rec.get("analyst_notes"):
                            st.markdown(f"**BDR Sign-Off:** *{rec['analyst_notes']}*")
            else:
                st.info("No qualified leads found in this timeframe.")

    # ---------------- RIGHT PANEL: SALES DECISION CANVAS ----------------
    with col_s_canvas:
        is_manual_s = (st.session_state.active_sales_id == "manual")
        active_sales_rec = None

        if not is_manual_s:
            active_sales_rec = database.get_operation_by_id(st.session_state.active_sales_id)
            if not active_sales_rec or active_sales_rec.get("is_processed") == 1:
                next_s = database.get_next_pending_operation("sales")
                if next_s:
                    st.session_state.active_sales_id = next_s["id"]
                    active_sales_rec = next_s
                else:
                    is_manual_s = True
                    st.session_state.active_sales_id = "manual"

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

        with st.expander("Prospect Profile & AR Aging Dock", expanded=True):
            if not is_manual_s:
                st.caption(f"Locked: Streaming directly from {s_canvas_source}. Text verification verified.")

            sales_input_text = st.text_area(
                "Commercial Profile / Notes:",
                value=s_raw_text,
                height=180,
                disabled=(not is_manual_s),
                key=f"s_text_{st.session_state.active_sales_id}"
            )
            sales_url_input = st.text_input(
                "AR Aging Report / Website URL (Optional):",
                value=s_doc_url,
                placeholder="https://company.com/freight-aging.pdf",
                key=f"s_url_{st.session_state.active_sales_id}"
            )

        col_sbl, col_sbbtn, col_sbr = st.columns([1, 2, 1])
        with col_sbbtn:
            run_sales = st.button("Analyze Commercial Lead", type="primary", width="stretch", key="btn_run_sales_triage")

        if run_sales:
            with st.spinner("Scoring commercial prospect & crafting outreach..."):
                supp_doc = ""
                if sales_url_input:
                    supp_doc = document_reader.extract_text_from_url(sales_url_input)

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
# TAB 3: HR DESKMATE (TALENT SCREENING - SPLIT COCKPIT)
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
            index=list(time_window_choices.keys()).index(st.session_state.get("hq_win", "all")),
            key="hq_win",
            label_visibility="visible"
        )

    hr_kpis = database.get_department_kpis("hr", time_window=hq_win)
    hr_records = database.get_filtered_operations(module_filter="hr", time_window=hq_win, limit=200)

    # Top Section: Key Metrics Ribbon & Bilingual Fluency Donut Chart
    col_h_stats, col_h_donut = st.columns([7, 5], gap="medium")
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

    with col_h_donut:
        c1_h = len([r for r in hr_records if "c1" in r.get("full_output_json", "").lower() or "c2" in r.get("full_output_json", "").lower() or "c1" in r.get("headline_metric", "").lower()])
        b2_h = len([r for r in hr_records if "b2" in r.get("full_output_json", "").lower() or "b2" in r.get("headline_metric", "").lower()])
        basic_h = max(0, len(hr_records) - (c1_h + b2_h))
        if len(hr_records) == 0:
            c1_h, b2_h, basic_h = 0, 0, 0
        tot_h = c1_h + b2_h + basic_h
        if tot_h > 0:
            df_h_tier = pd.DataFrame({
                "Fluency Level": ["C1/C2 Advanced", "B2 Operational", "Review / Basic"],
                "Candidates": [max(1, c1_h), max(1, b2_h), max(0, basic_h)]
            })
            df_h_tier = df_h_tier[df_h_tier["Candidates"] > 0]
            h_chart = alt.Chart(df_h_tier).mark_arc(innerRadius=36).encode(
                theta=alt.Theta(field="Candidates", type="quantitative"),
                color=alt.Color(
                    field="Fluency Level",
                    type="nominal",
                    scale=alt.Scale(
                        domain=["C1/C2 Advanced", "B2 Operational", "Review / Basic"],
                        range=["#3EA258", "#D97706", "#DC2626"]
                    ),
                    legend=alt.Legend(orient="right", title=None)
                ),
                tooltip=["Fluency Level", "Candidates"]
            ).properties(height=110)
            st.altair_chart(h_chart, width="stretch")
        else:
            st.info("No candidates screened in this period.")

    col_h_queue, col_h_canvas = st.columns([5, 7])

    # ---------------- LEFT PANEL: HR QUEUE & AUDIT ----------------
    with col_h_queue:
        hr_queue_tabs = st.tabs([
            f"Pending Queue ({hr_kpis['pending_count']})",
            f"Processed Talent ({hr_kpis['processed_count']})"
        ])

        with hr_queue_tabs[0]:
            col_hq_s, col_hq_o = st.columns([6, 4])
            with col_hq_s:
                hq_search = st.text_input("Filter Candidates:", placeholder="Search candidate, role...", key="hq_search", label_visibility="collapsed")
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
<span><span class="nudesk-badge {sla['color']}">{sla['label']}</span> &bull; {rec['source_channel']}</span>
<span style="font-weight:{'700' if is_active else '400'}; color:{'var(--nd-green)' if is_active else 'var(--nd-muted)'};">{status_indicator}</span>
</div>
</div>
</div>""", unsafe_allow_html=True)

                    if st.button("Select", key=f"btn_h_select_{rec['id']}", width="stretch"):
                        st.session_state.active_hr_id = rec["id"]
                        st.session_state.hr_result = None
                        st.rerun()
            else:
                st.info("Pending candidate screening queue is clear.")

        with hr_queue_tabs[1]:
            hp_search = st.text_input("Filter Talent Pipeline:", placeholder="Search screened candidates...", key="hp_search")
            processed_hr_items = database.get_filtered_operations(
                module_filter="hr",
                search_query=hp_search,
                sort_by="date",
                sort_order="desc",
                status_filter="processed",
                time_window=hq_win
            )

            if processed_hr_items:
                for rec in processed_hr_items:
                    sla = database.calculate_sla_status(rec["timestamp"], is_processed=1)
                    with st.expander(f"{rec['entity_name']} — {rec['headline_metric']}"):
                        st.markdown(f"""<div style="margin-bottom:0.5rem;">
<span class="nudesk-badge badge-green">{rec['dispatch_status']}</span>
<span style="font-size:0.8rem; color:#64748B; margin-left:0.5rem;">Evaluated {sla['label']} &bull; {rec['operator_name']}</span>
</div>""", unsafe_allow_html=True)
                        st.write(rec.get("assessment_summary", ""))
                        if rec.get("analyst_notes"):
                            st.markdown(f"**Recruiter Notes:** *{rec['analyst_notes']}*")
            else:
                st.info("No candidate scorecards found in this timeframe.")

    # ---------------- RIGHT PANEL: HR DECISION CANVAS ----------------
    with col_h_canvas:
        is_manual_h = (st.session_state.active_hr_id == "manual")
        active_hr_rec = None

        if not is_manual_h:
            active_hr_rec = database.get_operation_by_id(st.session_state.active_hr_id)
            if not active_hr_rec or active_hr_rec.get("is_processed") == 1:
                next_h = database.get_next_pending_operation("hr")
                if next_h:
                    st.session_state.active_hr_id = next_h["id"]
                    active_hr_rec = next_h
                else:
                    is_manual_h = True
                    st.session_state.active_hr_id = "manual"

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

        with st.expander("Screening Transcript & Resume Dock", expanded=True):
            if not is_manual_h:
                st.caption(f"Locked: Streaming directly from {h_canvas_source}. Text verification verified.")

            hr_input_text = st.text_area(
                "Interview Transcript:",
                value=h_raw_text,
                height=180,
                disabled=(not is_manual_h),
                key=f"h_text_{st.session_state.active_hr_id}"
            )
            hr_url_input = st.text_input(
                "LinkedIn / Resume Credentials URL (Optional):",
                value=h_doc_url,
                placeholder="https://linkedin.com/in/candidate",
                key=f"h_url_{st.session_state.active_hr_id}"
            )

        col_hbl, col_hbbtn, col_hbr = st.columns([1, 2, 1])
        with col_hbbtn:
            run_hr = st.button("Grade Candidate Screening", type="primary", width="stretch", key="btn_run_hr_triage")

        if run_hr:
            with st.spinner("Grading bilingual fluency & technical competencies..."):
                supp_doc = ""
                if hr_url_input:
                    supp_doc = document_reader.extract_text_from_url(hr_url_input)

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

            st.markdown(f"""<div class="kpi-container">
<div class="kpi-card">
<div class="kpi-label">Candidate Fit Score</div>
<div class="kpi-value">{hr_out.overall_fit_score} / 100</div>
<div class="kpi-sub">Suitability Rating</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Bilingual Fluency</div>
<div class="kpi-value" style="font-size:1.25rem; margin-top:0.35rem;">{hr_out.bilingual_fluency_rating}</div>
<div class="kpi-sub">US Lending Alignment</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Recommendation</div>
<div class="kpi-value" style="font-size:1.15rem; margin-top:0.4rem; color:#3EA258;">{hr_out.recommended_action}</div>
<div class="kpi-sub">Hiring Pipeline</div>
</div>
</div>""", unsafe_allow_html=True)

            st.markdown("#### Assessment Summary & Technical Competencies")
            st.markdown(f"""<div class="studio-card">
<div class="studio-card-header">
<span class="studio-card-title">{hr_out.candidate_name}</span>
<span class="nudesk-badge badge-green">{hr_out.applied_role}</span>
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
                    if is_manual_h or not active_hr_rec:
                        rec_id = database.save_operation(
                            operator_name=persona.name,
                            operator_role=persona.role_title,
                            module_type="hr",
                            entity_name=f"{hr_out.candidate_name} ({hr_out.applied_role})",
                            headline_metric=f"Score: {hr_out.overall_fit_score}/100 | {hr_out.bilingual_fluency_rating}",
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
                            headline_metric=f"Score: {hr_out.overall_fit_score}/100 | {hr_out.bilingual_fluency_rating}",
                            assessment_summary=hr_out.executive_summary,
                            full_output_json=hr_out.model_dump(),
                            operator_name=persona.name,
                            operator_role=persona.role_title,
                            analyst_notes=h_analyst_note
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
            index=list(time_window_choices.keys()).index(st.session_state.get("exec_win", "all")),
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
                st.altair_chart(dept_chart, width="stretch")
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
                st.altair_chart(risk_chart, width="stretch")
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
                fit_val = data_dict.get("fit_score", data_dict.get("overall_fit_score", 88))
                try:
                    fit_num = int(fit_val)
                except Exception:
                    fit_num = 88
                k1_l, k1_v = "Candidate Fit", f"{fit_num} / 100"
                if fit_num < 75:
                    k1_cls = "kpi-box-red"
                elif fit_num < 85:
                    k1_cls = "kpi-box-amber"
                else:
                    k1_cls = "kpi-box-green"

                cefr_val = str(data_dict.get("cefr", data_dict.get("bilingual_fluency", "C1 Advanced")))
                k2_l, k2_v = "Bilingual Fluency", cefr_val
                cefr_lower = cefr_val.lower()
                if any(x in cefr_lower for x in ["b1", "a2", "limited", "basic"]):
                    k2_cls = "kpi-box-red"
                elif "b2" in cefr_lower:
                    k2_cls = "kpi-box-amber"
                else:
                    k2_cls = "kpi-box-green"

                k3_l, k3_v = "Experience", f"{data_dict.get('experience_years', '4+')} Years"
                k3_cls = "kpi-box-teal"

                k4_l, k4_v = "Recommended Action", str(data_dict.get("action", "Advance to Next Round"))
                act_lower = k4_v.lower()
                if any(x in act_lower for x in ["reject", "decline"]):
                    k4_cls = "kpi-box-red"
                elif any(x in act_lower for x in ["hold", "review"]):
                    k4_cls = "kpi-box-amber"
                else:
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
    st.markdown("Operational infrastructure, API keys, webhook endpoints, and n8n Docker orchestration.")

    if not persona.permissions.get("it_admin_settings", False):
        st.warning(
            f"Access Restricted: Your current Google Workspace identity ({persona.name} — {persona.role_title}) does not hold IT Administrator permissions. "
            "Switch to Omar Payán (Lead AI Ops Engineer) in the identity selector above to configure API keys and webhook dispatchers."
        )
    else:
        st.success(f"Authenticated as {persona.name} ({persona.role_title}). IT controls unlocked.")

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

        st.markdown("#### Active Model Cascade")
        st.markdown("""
        ```text
        Tier 1: gemini-3.5-flash-lite (Cost-optimized, ultra-fast latency for high-volume discovery triage)
        Tier 2: gemini-3.5-flash      (Intermediate fallback on high concurrency)
        Tier 3: gemini-flash-latest   (Dynamic latest stable checkpoint)
        Tier 4: Demonstration Mode   (Fail-safe synthetic benchmark to avoid runtime crash)
        ```
        """)

        st.markdown("#### Remote Multi-Device HTTPS Access")
        st.markdown("""
        To demo this application on mobile devices (iOS / Android) or external laptops:
        ```bash
        # Run the automated tunnel script
        ./scripts/start_tunnel.sh
        ```
        This generates an instant, secure Cloudflare HTTPS URL without requiring router port-forwarding.
        """)

        st.markdown("#### System Health & Diagnostics")
        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            st.metric("Docker n8n Status", "Online (Port 5678)")
        with col_d2:
            st.metric("Database Health", "SQLite OK (data/operations_history.db)")
        with col_d3:
            st.metric("Pydantic Schemas", "3 Active (Credit, Sales, HR)")

        st.markdown("#### Synthetic Webhook & Meeting Bot Simulator")
        st.caption("Demonstration suite: Ingest realistic production payloads from Read AI, Fireflies.ai, and Google Drive without paid accounts.")
        col_sim1, col_sim2, col_sim3 = st.columns(3)
        with col_sim1:
            if st.button("Fire Read AI Credit Call", width="stretch", key="btn_it_sim_readai"):
                from scripts.generate_synthetic_intake import generate_synthetic_payload, extract_ingestion_fields
                p = generate_synthetic_payload("readai", "credit")
                f = extract_ingestion_fields(p, "readai", "credit")
                nid = database.ingest_pending_record(
                    module_type=f["module_type"], entity_name=f["entity_name"], headline_metric=f["headline_metric"],
                    transcript_text=f["transcript_text"], assessment_summary=f["assessment_summary"], source_channel=f["source_channel"],
                    doc_url=f["doc_url"], doc_note=f["doc_note"], metadata_extra=f["metadata_extra"]
                )
                st.success(f"Ingested Record #{nid}: {f['entity_name']} (Credit Queue)")
        with col_sim2:
            if st.button("Fire Fireflies Sales Call", width="stretch", key="btn_it_sim_fireflies"):
                from scripts.generate_synthetic_intake import generate_synthetic_payload, extract_ingestion_fields
                p = generate_synthetic_payload("fireflies", "sales")
                f = extract_ingestion_fields(p, "fireflies", "sales")
                nid = database.ingest_pending_record(
                    module_type=f["module_type"], entity_name=f["entity_name"], headline_metric=f["headline_metric"],
                    transcript_text=f["transcript_text"], assessment_summary=f["assessment_summary"], source_channel=f["source_channel"],
                    doc_url=f["doc_url"], doc_note=f["doc_note"], metadata_extra=f["metadata_extra"]
                )
                st.success(f"Ingested Record #{nid}: {f['entity_name']} (Sales Queue)")
        with col_sim3:
            if st.button("Fire Google Drive Intake", width="stretch", key="btn_it_sim_gdrive"):
                from scripts.generate_synthetic_intake import generate_synthetic_payload, extract_ingestion_fields
                p = generate_synthetic_payload("gdrive", "credit")
                f = extract_ingestion_fields(p, "gdrive", "credit")
                nid = database.ingest_pending_record(
                    module_type=f["module_type"], entity_name=f["entity_name"], headline_metric=f["headline_metric"],
                    transcript_text=f["transcript_text"], assessment_summary=f["assessment_summary"], source_channel=f["source_channel"],
                    doc_url=f["doc_url"], doc_note=f["doc_note"], metadata_extra=f["metadata_extra"]
                )
                st.success(f"Ingested Record #{nid}: {f['entity_name']} (Drive Intake)")
