"""
DeskMate Operations Studio V2
nuDesk MX — Mazatlán Operations Hub & US Commercial Lending
AI-Workforce Platform for Financial Services
"""
import os
import json
import streamlit as st
from dotenv import load_dotenv

# Internal modular imports
from styles.nudesk_theme import get_nudesk_css
import auth_rbac
from auth_rbac import PRESET_WORKSPACE_PERSONAS
from meeting_queue import INCOMING_MEETINGS_QUEUE
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

# Selected queue preloads
if "credit_selected_inbox" not in st.session_state:
    st.session_state.credit_selected_inbox = None
if "sales_selected_inbox" not in st.session_state:
    st.session_state.sales_selected_inbox = None
if "hr_selected_inbox" not in st.session_state:
    st.session_state.hr_selected_inbox = None

# Environment credentials (Managed by IT)
current_api_key = os.getenv("GEMINI_API_KEY", "")
current_webhook_url = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/nudesk-triage")

# ----------------- CLEAN BRAND HEADER -----------------
is_google_active = st.session_state.google_user is not None
google_status_html = '<span class="nudesk-badge badge-green">Google Workspace Connected</span>' if is_google_active else ''
header_right_html = f'<div style="display:flex; gap:0.5rem; align-items:center;">{google_status_html}</div>' if google_status_html else ''

st.markdown(f"""<div class="nudesk-header">
<div>
<h1>nuDesk | DeskMate Operations Studio</h1>
<div class="subtitle">AI-Workforce Platform for Financial Services — Mazatlán Talent Hub</div>
</div>
{header_right_html}
</div>""", unsafe_allow_html=True)

# ----------------- WORKSPACE IDENTITY & TIME WINDOW BANNER -----------------
col_user, col_switch, col_window, col_theme = st.columns([3, 2, 2, 1])

with col_user:
    badge_label = "Google Workspace" if is_google_active else f"Role: {persona.role_key.upper()}"
    badge_cls = "badge-green" if is_google_active else "badge-navy"

    if persona.picture_url:
        avatar_html = f'<img src="{persona.picture_url}" style="width:28px; height:28px; border-radius:50%; border:2px solid #3EA258; vertical-align:middle; margin-right:8px;" />'
    else:
        avatar_html = f'<span class="role-avatar">{persona.avatar_initials}</span>'

    st.markdown(f"""<div class="role-banner">
<div class="role-indicator">
{avatar_html}
<span>{persona.name} &bull; <strong>{persona.role_title}</strong> <span style="color:#64748B;">({persona.email})</span></span>
</div>
<div>
<span class="nudesk-badge {badge_cls}">{badge_label}</span>
</div>
</div>""", unsafe_allow_html=True)

    if is_google_active:
        if st.button("Sign out of Google", key="btn_signout_google", use_container_width=True):
            st.session_state.google_user = None
            st.session_state.authenticated_persona = None
            st.session_state.active_persona_id = "usr_underwriter_1"
            st.rerun()
    elif google_client_id:
        auth_url = auth_rbac.get_google_auth_url(google_client_id, google_redirect_uri)
        st.link_button("Sign in with Google Workspace", auth_url, use_container_width=True)

with col_switch:
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
        "Workspace Identity (RBAC):",
        options=list(persona_options.keys()),
        format_func=lambda pid: persona_options[pid],
        index=list(persona_options.keys()).index(current_id),
        help="Simulates Google Workspace SSO identity. Changing role reconfigures permissions and access."
    )
    if selected_persona_id != st.session_state.active_persona_id:
        st.session_state.active_persona_id = selected_persona_id
        st.rerun()

with col_window:
    time_window_choices = {
        "week": "This Week (Rolling 7 Days)",
        "today": "Today",
        "month": "This Month (MTD)",
        "all": "All Time"
    }
    selected_tw_key = st.selectbox(
        "Operational Time Window:",
        options=list(time_window_choices.keys()),
        format_func=lambda k: time_window_choices[k],
        index=list(time_window_choices.keys()).index(st.session_state.time_window),
        help="Filters KPIs and audit trails to the selected operational timeframe."
    )
    if selected_tw_key != st.session_state.time_window:
        st.session_state.time_window = selected_tw_key
        st.rerun()

with col_theme:
    theme_choice = st.selectbox(
        "Theme:",
        ["Light", "Dark"],
        index=0 if st.session_state.current_theme == "light" else 1,
        help="Toggle high-contrast nuDesk Light or Dark palette."
    )
    chosen_theme_key = theme_choice.lower()
    if chosen_theme_key != st.session_state.current_theme:
        st.session_state.current_theme = chosen_theme_key
        st.rerun()


# ----------------- REUSABLE OPERATION LOG RENDERER -----------------
def render_operational_queue(
    records: list,
    is_pending: bool,
    module_key: str,
    key_prefix: str
):
    """Render single-line expandable operational logs with full underwriting memo & JSON on expand."""
    if not records:
        empty_msg = "No pending intake items in this queue." if is_pending else "No processed operations recorded in this timeframe."
        st.info(empty_msg)
        return

    for rec in records:
        status_label = rec.get("dispatch_status", "Synced")
        badge_cls = "badge-teal" if is_pending else "badge-green"
        entity_title = rec.get("entity_name", "Unknown Entity")
        metric_str = rec.get("headline_metric", "")
        time_str = rec.get("timestamp", "")
        summary_text = rec.get("assessment_summary", "")
        source_str = rec.get("source_channel", "Google Meet / Read AI")
        operator_str = f"{rec.get('operator_name', 'Operator')} ({rec.get('operator_role', '')})"

        # Single-line card summary
        expander_label = f"{entity_title}   |   {metric_str}   |   {time_str}"
        with st.expander(expander_label, expanded=False):
            st.markdown(f"""<div style="margin-bottom:0.75rem;">
<span class="nudesk-badge {badge_cls}">{status_label}</span>
<span style="font-size:0.85rem; color:#64748B; margin-left:0.75rem;">Source: {source_str} &bull; Handled by: {operator_str}</span>
</div>""", unsafe_allow_html=True)

            col_detail, col_payload = st.columns([3, 2])
            with col_detail:
                st.markdown("**Executive Assessment / Ingestion Notes:**")
                st.write(summary_text)

                if is_pending:
                    if st.button("Load Call into Triage Workspace", key=f"{key_prefix}_load_{rec['id']}", type="secondary"):
                        st.session_state[f"{module_key}_selected_inbox"] = rec["entity_name"]
                        st.rerun()

            with col_payload:
                st.markdown("**Structured Data Payload:**")
                try:
                    raw_data = json.loads(rec.get("full_output_json", "{}"))
                    st.json(raw_data)
                except Exception:
                    st.text(rec.get("full_output_json", ""))


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
# TAB 1: CREDIT DESKMATE (UNDERWRITING DISCOVERY TRIAGE)
# =========================================================================
with tabs[0]:
    st.markdown("### Credit Operations — Post-Call Discovery Triage")
    st.markdown(
        "Automated financial extraction, debt-to-income calculation, and Asana checklist staging. "
        "*Underwriters spend time on judgment, not data entry.*"
    )

    # Departmental KPIs for Credit
    credit_kpis = database.get_department_kpis("credit", time_window=st.session_state.time_window)
    st.markdown(f"""<div class="kpi-container">
<div class="kpi-card">
<div class="kpi-label">Pending Intake Queue</div>
<div class="kpi-value">{credit_kpis['pending_count']}</div>
<div class="kpi-sub">Oldest calls prioritized (FIFO)</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Processed Underwriting Memos</div>
<div class="kpi-value">{credit_kpis['processed_count']}</div>
<div class="kpi-sub">Synced to LOS & Asana</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Avg Underwriting Time Saved</div>
<div class="kpi-value">~38 min</div>
<div class="kpi-sub">Per equipment/factoring file</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Timeframe Active</div>
<div class="kpi-value" style="font-size:1.15rem; margin-top:0.4rem;">{time_window_choices[st.session_state.time_window]}</div>
<div class="kpi-sub">Mazatlán Lending Desk</div>
</div>
</div>""", unsafe_allow_html=True)

    # Dual Log Queues
    st.markdown("#### Operational Activity Log")
    credit_log_tabs = st.tabs([
        f"Pending Intake Queue ({credit_kpis['pending_count']})",
        f"Processed Operations ({credit_kpis['processed_count']})"
    ])

    # --- PENDING QUEUE (Default: Oldest First) ---
    with credit_log_tabs[0]:
        col_csearch, col_csort, col_corder = st.columns([3, 2, 2])
        with col_csearch:
            c_psearch = st.text_input("Search Pending Queue:", placeholder="Filter by company, applicant, or note...", key="c_psearch")
        with col_csort:
            c_psort = st.selectbox("Sort By:", ["Date / Time", "Entity Name", "Metric"], index=0, key="c_psort")
        with col_corder:
            c_porder = st.selectbox("Sort Order:", ["Oldest First (FIFO Priority)", "Newest First"], index=0, key="c_porder")

        sort_field = "name" if c_psort == "Entity Name" else ("metric" if c_psort == "Metric" else "date")
        sort_dir = "asc" if "Oldest" in c_porder else "desc"

        pending_credit_records = database.get_filtered_operations(
            module_filter="credit",
            search_query=c_psearch,
            sort_by=sort_field,
            sort_order=sort_dir,
            status_filter="pending",
            time_window=st.session_state.time_window
        )
        render_operational_queue(pending_credit_records, is_pending=True, module_key="credit", key_prefix="c_pend")

    # --- PROCESSED QUEUE (Default: Newest First) ---
    with credit_log_tabs[1]:
        col_cp_search, col_cp_sort, col_cp_order = st.columns([3, 2, 2])
        with col_cp_search:
            c_done_search = st.text_input("Search Processed Memos:", placeholder="Filter by company, underwriter, or status...", key="c_dsearch")
        with col_cp_sort:
            c_done_sort = st.selectbox("Sort By:", ["Date / Time", "Entity Name", "Metric"], index=0, key="c_dsort")
        with col_cp_order:
            c_done_order = st.selectbox("Sort Order:", ["Newest First", "Oldest First"], index=0, key="c_dorder")

        sort_field = "name" if c_done_sort == "Entity Name" else ("metric" if c_done_sort == "Metric" else "date")
        sort_dir = "asc" if "Oldest" in c_done_order else "desc"

        processed_credit_records = database.get_filtered_operations(
            module_filter="credit",
            search_query=c_done_search,
            sort_by=sort_field,
            sort_order=sort_dir,
            status_filter="processed",
            time_window=st.session_state.time_window
        )
        render_operational_queue(processed_credit_records, is_pending=False, module_key="credit", key_prefix="c_done")

    st.markdown("---")

    # --- INTAKE & POST-CALL TRIAGE WORKSPACE ---
    st.markdown("#### Post-Call Triage Workspace")
    credit_meetings = [m for m in INCOMING_MEETINGS_QUEUE if m["type"] == "credit"]
    meeting_titles = ["Manual Transcript Paste / Ad-hoc Call"] + [f"Inbox: {m['title']} ({m['source']} - {m['received_ago']})" for m in credit_meetings]

    # Pre-select if triggered from queue
    default_c_idx = 1 if credit_meetings else 0
    if st.session_state.credit_selected_inbox:
        for idx, title in enumerate(meeting_titles):
            if st.session_state.credit_selected_inbox in title:
                default_c_idx = idx
                break

    selected_credit_meet = st.selectbox(
        "Call Ingestion Source (Google Meet / Read AI / Fireflies):",
        meeting_titles,
        index=default_c_idx,
        help="Automated streams ingest transcripts directly from meeting bots with locked raw text."
    )

    is_automated_credit = (selected_credit_meet != "Manual Transcript Paste / Ad-hoc Call")
    if is_automated_credit:
        chosen_meeting = credit_meetings[0]
        for m in credit_meetings:
            if m["title"] in selected_credit_meet or m["entity"] in selected_credit_meet:
                chosen_meeting = m
                break
        default_credit_text = chosen_meeting["transcript"]
        default_doc_url = chosen_meeting["default_doc_url"]
        default_doc_notes = chosen_meeting["doc_note"]
    else:
        default_credit_text = BENCHMARK_TRANSCRIPT
        default_doc_url = ""
        default_doc_notes = ""

    # Workspace form
    with st.expander("Discovery Call Transcript & Collateral", expanded=True):
        if is_automated_credit:
            st.caption("Status: Pending Intake (Unprocessed) — Locked automated stream from Google Meet via Read AI.")

        credit_input_text = st.text_area(
            "Raw Call Transcript:",
            value=default_credit_text,
            height=200,
            disabled=is_automated_credit
        )

        col_curl, col_cupload = st.columns([2, 1])
        with col_curl:
            quote_url_input = st.text_input(
                "Supporting Document / Quote URL (Optional):",
                value=default_doc_url,
                placeholder="https://vendor.com/equipment-quote-85k.pdf"
            )
        with col_cupload:
            uploaded_doc = st.file_uploader(
                "Or Upload Financial File (PDF / CSV):",
                type=["txt", "pdf", "csv", "md"],
                key="c_file_upload"
            )

        if default_doc_notes:
            st.caption(f"Verified Attachment: {default_doc_notes}")

    # Centered Minimal Button
    col_cl, col_cbtn, col_cr = st.columns([1, 2, 1])
    with col_cbtn:
        run_credit = st.button("Run Credit Triage", type="primary", use_container_width=True)

    if run_credit:
        with st.spinner("Analyzing transcript and reconciling collateral with Gemini..."):
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

    # Display Triage Results
    if st.session_state.credit_result:
        credit_out: CreditTriageOutput = st.session_state.credit_result[0]
        is_fallback = st.session_state.credit_result[1]
        status_msg = st.session_state.credit_result[2]

        if is_fallback:
            st.info(f"Demonstration Benchmark Mode: {status_msg}")
        else:
            st.success(f"{status_msg}")

        # KPI Metrics Display
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-card">
                <div class="kpi-label">Risk Assessment</div>
                <div class="kpi-value">{credit_out.risk_tier}</div>
                <div class="kpi-sub">Underwriting Committee Tier</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Requested Capital</div>
                <div class="kpi-value">${credit_out.loan_amount_requested_usd:,.0f} <span style="font-size:0.9rem;">USD</span></div>
                <div class="kpi-sub">Equipment Term Financing</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Stated Monthly Rev</div>
                <div class="kpi-value">${credit_out.stated_monthly_revenue_usd:,.0f} <span style="font-size:0.9rem;">USD</span></div>
                <div class="kpi-sub">Verified Gross Billings</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Estimated DTI</div>
                <div class="kpi-value">{credit_out.estimated_dti_ratio * 100:.1f}%</div>
                <div class="kpi-sub">Debt-to-Income Ratio</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_memo, col_tasks = st.columns([3, 2])

        with col_memo:
            st.markdown("#### Executive Underwriting Memo")
            st.markdown(f"""
            <div class="studio-card">
                <div class="studio-card-header">
                    <span class="studio-card-title">{credit_out.business_name} ({credit_out.applicant_name})</span>
                    <span class="nudesk-badge badge-navy">{credit_out.industry}</span>
                </div>
                <p style="color:var(--nd-text); font-size:0.92rem; line-height:1.6;">{credit_out.executive_summary}</p>
                
                <h5 style="margin-top:1rem; margin-bottom:0.5rem; color:#A31D1D;">Identified Underwriting Red Flags:</h5>
            """, unsafe_allow_html=True)

            if credit_out.red_flags:
                for flag in credit_out.red_flags:
                    st.markdown(f'<div class="flag-item">&bull; {flag}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#3EA258;">No critical red flags identified.</p>', unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        with col_tasks:
            st.markdown("#### Asana Operational Tasks")
            for task in credit_out.asana_tasks:
                badge_class = "badge-red" if task.priority == "High" else "badge-teal"
                st.markdown(f"""
                <div class="task-item">
                    <div>
                        <div class="task-title">{task.task_title}</div>
                        <div style="margin-top:0.25rem;"><span class="task-assignee">{task.assignee_role}</span></div>
                    </div>
                    <div>
                        <span class="nudesk-badge {badge_class}">{task.priority}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Operational Approval & Auto-Persistence
        col_apl, col_apbtn, col_apr = st.columns([1, 2, 1])
        with col_apbtn:
            if st.button("Approve & Sync Credit Memo to Pipeline", type="primary", use_container_width=True):
                rec_id = database.save_operation(
                    operator_name=persona.name,
                    operator_role=persona.role_title,
                    module_type="credit",
                    entity_name=f"{credit_out.business_name} ({credit_out.applicant_name})",
                    headline_metric=f"{credit_out.risk_tier} | ${credit_out.loan_amount_requested_usd:,.0f} USD",
                    assessment_summary=credit_out.executive_summary,
                    full_output_json=credit_out.model_dump(),
                    dispatch_status="Synced to n8n / LOS",
                    is_processed=1,
                    source_channel="Google Meet / Read AI"
                )

                # Dispatch via HTTP to n8n
                ok, disp_msg, _ = crm_dispatcher.dispatch_to_n8n(
                    webhook_url=current_webhook_url,
                    payload=credit_out.model_dump(),
                    flow_type="credit"
                )

                st.session_state.credit_selected_inbox = None
                if ok:
                    st.success(f"Audit Record #{rec_id} saved. File successfully dispatched to n8n Underwriting Pipeline.")
                else:
                    st.success(f"Audit Record #{rec_id} saved locally. Dispatch note: {disp_msg}")
                st.rerun()

# =========================================================================
# TAB 2: SALES DESKMATE (COMMERCIAL BDR LEAD SCORING & OUTREACH)
# =========================================================================
with tabs[1]:
    st.markdown("### Sales Operations — Commercial BDR Lead Scoring & Outreach")
    st.markdown(
        "Commercial profile qualification, factoring fit evaluation, and personalized speed-to-lead dialing assets. "
        "*Arming Mazatlán BDRs with high-conversion outreach in seconds.*"
    )

    # Departmental KPIs for Sales
    sales_kpis = database.get_department_kpis("sales", time_window=st.session_state.time_window)
    st.markdown(f"""<div class="kpi-container">
<div class="kpi-card">
<div class="kpi-label">Pending Lead Queue</div>
<div class="kpi-value">{sales_kpis['pending_count']}</div>
<div class="kpi-sub">Oldest leads prioritized (FIFO)</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Qualified Commercial Leads</div>
<div class="kpi-value">{sales_kpis['processed_count']}</div>
<div class="kpi-sub">Synced to CRM & Gmail</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Avg Lead Fit Score</div>
<div class="kpi-value">86 / 100</div>
<div class="kpi-sub">Factoring & term lines</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Timeframe Active</div>
<div class="kpi-value" style="font-size:1.15rem; margin-top:0.4rem;">{time_window_choices[st.session_state.time_window]}</div>
<div class="kpi-sub">Mazatlán BDR Desk</div>
</div>
</div>""", unsafe_allow_html=True)

    # Dual Log Queues
    st.markdown("#### Operational Activity Log")
    sales_log_tabs = st.tabs([
        f"Pending Lead Queue ({sales_kpis['pending_count']})",
        f"Processed Leads ({sales_kpis['processed_count']})"
    ])

    with sales_log_tabs[0]:
        col_ssearch, col_ssort, col_sorder = st.columns([3, 2, 2])
        with col_ssearch:
            s_psearch = st.text_input("Search Pending Leads:", placeholder="Filter by company, fleet, or notes...", key="s_psearch")
        with col_ssort:
            s_psort = st.selectbox("Sort By:", ["Date / Time", "Entity Name", "Metric"], index=0, key="s_psort")
        with col_sorder:
            s_porder = st.selectbox("Sort Order:", ["Oldest First (FIFO Priority)", "Newest First"], index=0, key="s_porder")

        sort_field = "name" if s_psort == "Entity Name" else ("metric" if s_psort == "Metric" else "date")
        sort_dir = "asc" if "Oldest" in s_porder else "desc"

        pending_sales_records = database.get_filtered_operations(
            module_filter="sales",
            search_query=s_psearch,
            sort_by=sort_field,
            sort_order=sort_dir,
            status_filter="pending",
            time_window=st.session_state.time_window
        )
        render_operational_queue(pending_sales_records, is_pending=True, module_key="sales", key_prefix="s_pend")

    with sales_log_tabs[1]:
        col_sp_search, col_sp_sort, col_sp_order = st.columns([3, 2, 2])
        with col_sp_search:
            s_done_search = st.text_input("Search Processed Leads:", placeholder="Filter by company, BDR, or status...", key="s_dsearch")
        with col_sp_sort:
            s_done_sort = st.selectbox("Sort By:", ["Date / Time", "Entity Name", "Metric"], index=0, key="s_dsort")
        with col_sp_order:
            s_done_order = st.selectbox("Sort Order:", ["Newest First", "Oldest First"], index=0, key="s_dorder")

        sort_field = "name" if s_done_sort == "Entity Name" else ("metric" if s_done_sort == "Metric" else "date")
        sort_dir = "asc" if "Oldest" in s_done_order else "desc"

        processed_sales_records = database.get_filtered_operations(
            module_filter="sales",
            search_query=s_done_search,
            sort_by=sort_field,
            sort_order=sort_dir,
            status_filter="processed",
            time_window=st.session_state.time_window
        )
        render_operational_queue(processed_sales_records, is_pending=False, module_key="sales", key_prefix="s_done")

    st.markdown("---")

    # --- SALES WORKSPACE ---
    st.markdown("#### Commercial Prospect Intake & Scoring")
    sales_meetings = [m for m in INCOMING_MEETINGS_QUEUE if m["type"] == "sales"]
    sales_titles = ["Manual Lead Profile Entry"] + [f"Inbox: {m['title']} ({m['source']} - {m['received_ago']})" for m in sales_meetings]

    default_s_idx = 1 if sales_meetings else 0
    if st.session_state.sales_selected_inbox:
        for idx, title in enumerate(sales_titles):
            if st.session_state.sales_selected_inbox in title:
                default_s_idx = idx
                break

    selected_sales_meet = st.selectbox(
        "Commercial Prospect Ingestion Source:",
        sales_titles,
        index=default_s_idx,
        help="Automated streams ingest transcripts directly from meeting bots with locked raw text."
    )

    is_automated_sales = (selected_sales_meet != "Manual Lead Profile Entry")
    if is_automated_sales:
        chosen_sales = sales_meetings[0]
        for m in sales_meetings:
            if m["title"] in selected_sales_meet or m["entity"] in selected_sales_meet:
                chosen_sales = m
                break
        default_sales_text = chosen_sales["lead_data"]
        default_sales_url = chosen_sales["default_doc_url"]
        default_sales_note = chosen_sales["doc_note"]
    else:
        default_sales_text = BENCHMARK_SALES_LEAD
        default_sales_url = ""
        default_sales_note = ""

    with st.expander("Prospect Profile & Collateral Information", expanded=True):
        if is_automated_sales:
            st.caption("Status: Pending Lead Qualification (Unprocessed) — Locked automated stream from Google Meet.")

        sales_input_text = st.text_area(
            "Raw Commercial Profile / Call Notes:",
            value=default_sales_text,
            height=180,
            disabled=is_automated_sales
        )
        sales_url_input = st.text_input(
            "Prospect AR Aging Report / Website URL (Optional):",
            value=default_sales_url,
            placeholder="https://company.com/freight-aging.pdf"
        )
        if default_sales_note:
            st.caption(f"Verified Collateral: {default_sales_note}")

    col_sl, col_sbtn, col_sr = st.columns([1, 2, 1])
    with col_sbtn:
        run_sales = st.button("Analyze Commercial Lead", type="primary", use_container_width=True)

    if run_sales:
        with st.spinner("Scoring commercial prospect and crafting outreach assets..."):
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

        # Metrics
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-card">
                <div class="kpi-label">Lead Qualification Score</div>
                <div class="kpi-value">{sales_out.lead_score} <span style="font-size:0.9rem;">/ 100</span></div>
                <div class="kpi-sub">Priority Outbound Tier</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Annual Revenue</div>
                <div class="kpi-value">${sales_out.annual_revenue_usd:,.0f} <span style="font-size:0.9rem;">USD</span></div>
                <div class="kpi-sub">Reported ARR / Billings</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Industry Sector</div>
                <div class="kpi-value" style="font-size:1.15rem; margin-top:0.4rem;">{sales_out.industry}</div>
                <div class="kpi-sub">Commercial Target</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_lead, col_script = st.columns([1, 1])

        with col_lead:
            st.markdown("#### Qualification Rationale & Cold Email Draft")
            st.markdown(f"""
            <div class="studio-card">
                <div class="studio-card-header">
                    <span class="studio-card-title">{sales_out.company_name}</span>
                    <span class="nudesk-badge badge-green">Contact: {sales_out.contact_person}</span>
                </div>
                <p style="color:var(--nd-text); font-size:0.88rem;"><strong>Score Rationale:</strong> {sales_out.score_rationale}</p>
                <div style="margin-top:0.75rem;">
                    <strong>Executive Cold Email (Gmail Draft Ready):</strong>
                    <div class="script-box">{sales_out.cold_email_en}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_script:
            st.markdown("#### 30-Second BDR Speed-to-Lead Phone Script")
            st.markdown(f"""
            <div class="studio-card">
                <div class="studio-card-header">
                    <span class="studio-card-title">Live Call Opening Script (Mazatlán BDRs)</span>
                    <span class="nudesk-badge badge-navy">English Pitch</span>
                </div>
                <p style="color:var(--nd-muted); font-size:0.82rem; margin-bottom:0.5rem;">
                    Designed for sub-10 second hook and immediate pain-point alignment.
                </p>
                <div class="script-box">{sales_out.phone_script_30s_en}</div>
            </div>
            """, unsafe_allow_html=True)

        # Operational Approval & Auto-Persistence
        col_sapl, col_sapbtn, col_sapr = st.columns([1, 2, 1])
        with col_sapbtn:
            if st.button("Sync Lead to CRM & Staged Drafts", type="primary", use_container_width=True):
                rec_id = database.save_operation(
                    operator_name=persona.name,
                    operator_role=persona.role_title,
                    module_type="sales",
                    entity_name=f"{sales_out.company_name} ({sales_out.contact_person})",
                    headline_metric=f"Score: {sales_out.lead_score}/100 | ${sales_out.annual_revenue_usd:,.0f} ARR",
                    assessment_summary=sales_out.score_rationale,
                    full_output_json=sales_out.model_dump(),
                    dispatch_status="Synced to n8n / Sales CRM",
                    is_processed=1,
                    source_channel="Google Meet / Read AI"
                )

                ok, disp_msg, _ = crm_dispatcher.dispatch_to_n8n(
                    webhook_url=current_webhook_url,
                    payload=sales_out.model_dump(),
                    flow_type="sales"
                )

                st.session_state.sales_selected_inbox = None
                if ok:
                    st.success(f"Audit Record #{rec_id} saved. Lead successfully synced to Sales CRM & BDR outbox.")
                else:
                    st.success(f"Audit Record #{rec_id} saved locally. Dispatch note: {disp_msg}")
                st.rerun()

# =========================================================================
# TAB 3: HR DESKMATE (TALENT SCREENING & BILINGUAL ASSESSMENT)
# =========================================================================
with tabs[2]:
    st.markdown("### HR & Talent Solutions — Candidate Interview Screening")
    st.markdown(
        "Bilingual interview evaluation, technical competency grading, and hiring manager case-study synthesis. "
        "*Reflecting nuDesk's actual candidate screening pipeline in Mazatlán.*"
    )

    # Departmental KPIs for HR
    hr_kpis = database.get_department_kpis("hr", time_window=st.session_state.time_window)
    st.markdown(f"""<div class="kpi-container">
<div class="kpi-card">
<div class="kpi-label">Pending Screening Queue</div>
<div class="kpi-value">{hr_kpis['pending_count']}</div>
<div class="kpi-sub">Oldest screenings prioritized (FIFO)</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Candidates Evaluated</div>
<div class="kpi-value">{hr_kpis['processed_count']}</div>
<div class="kpi-sub">Synced to Talent Pipeline</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Average Fit Score</div>
<div class="kpi-value">89 / 100</div>
<div class="kpi-sub">C1/C2 bilingual proficiency</div>
</div>
<div class="kpi-card">
<div class="kpi-label">Timeframe Active</div>
<div class="kpi-value" style="font-size:1.15rem; margin-top:0.4rem;">{time_window_choices[st.session_state.time_window]}</div>
<div class="kpi-sub">Mazatlán Recruiting Hub</div>
</div>
</div>""", unsafe_allow_html=True)

    # Dual Log Queues
    st.markdown("#### Operational Activity Log")
    hr_log_tabs = st.tabs([
        f"Pending Screening Queue ({hr_kpis['pending_count']})",
        f"Processed Talent ({hr_kpis['processed_count']})"
    ])

    with hr_log_tabs[0]:
        col_hr_search, col_hr_sort, col_hr_order = st.columns([3, 2, 2])
        with col_hr_search:
            hr_psearch = st.text_input("Search Pending Screenings:", placeholder="Filter by candidate, role, or skill...", key="hr_psearch")
        with col_hr_sort:
            hr_psort = st.selectbox("Sort By:", ["Date / Time", "Entity Name", "Metric"], index=0, key="hr_psort")
        with col_hr_order:
            hr_porder = st.selectbox("Sort Order:", ["Oldest First (FIFO Priority)", "Newest First"], index=0, key="hr_porder")

        sort_field = "name" if hr_psort == "Entity Name" else ("metric" if hr_psort == "Metric" else "date")
        sort_dir = "asc" if "Oldest" in hr_porder else "desc"

        pending_hr_records = database.get_filtered_operations(
            module_filter="hr",
            search_query=hr_psearch,
            sort_by=sort_field,
            sort_order=sort_dir,
            status_filter="pending",
            time_window=st.session_state.time_window
        )
        render_operational_queue(pending_hr_records, is_pending=True, module_key="hr", key_prefix="hr_pend")

    with hr_log_tabs[1]:
        col_hr_dsearch, col_hr_dsort, col_hr_dorder = st.columns([3, 2, 2])
        with col_hr_dsearch:
            hr_done_search = st.text_input("Search Processed Screenings:", placeholder="Filter by candidate, recruiter, or score...", key="hr_dsearch")
        with col_hr_dsort:
            hr_done_sort = st.selectbox("Sort By:", ["Date / Time", "Entity Name", "Metric"], index=0, key="hr_dsort")
        with col_hr_dorder:
            hr_done_order = st.selectbox("Sort Order:", ["Newest First", "Oldest First"], index=0, key="hr_dorder")

        sort_field = "name" if hr_done_sort == "Entity Name" else ("metric" if hr_done_sort == "Metric" else "date")
        sort_dir = "asc" if "Oldest" in hr_done_order else "desc"

        processed_hr_records = database.get_filtered_operations(
            module_filter="hr",
            search_query=hr_done_search,
            sort_by=sort_field,
            sort_order=sort_dir,
            status_filter="processed",
            time_window=st.session_state.time_window
        )
        render_operational_queue(processed_hr_records, is_pending=False, module_key="hr", key_prefix="hr_done")

    st.markdown("---")

    # --- HR WORKSPACE ---
    st.markdown("#### Candidate Screening & Assessment")
    hr_meetings = [m for m in INCOMING_MEETINGS_QUEUE if m["type"] == "hr"]
    hr_titles = ["Manual Interview Transcript Paste"] + [f"Inbox: {m['title']} ({m['source']} - {m['received_ago']})" for m in hr_meetings]

    default_hr_idx = 1 if hr_meetings else 0
    if st.session_state.hr_selected_inbox:
        for idx, title in enumerate(hr_titles):
            if st.session_state.hr_selected_inbox in title:
                default_hr_idx = idx
                break

    selected_hr_meet = st.selectbox(
        "Candidate Interview Ingestion Source:",
        hr_titles,
        index=default_hr_idx,
        help="Automated streams ingest transcripts directly from meeting bots with locked raw text."
    )

    is_automated_hr = (selected_hr_meet != "Manual Interview Transcript Paste")
    if is_automated_hr:
        chosen_hr = hr_meetings[0]
        for m in hr_meetings:
            if m["title"] in selected_hr_meet or m["entity"] in selected_hr_meet:
                chosen_hr = m
                break
        default_hr_text = chosen_hr["transcript"]
        default_hr_doc = chosen_hr["default_doc_url"]
        default_hr_note = chosen_hr["doc_note"]
    else:
        default_hr_text = BENCHMARK_HR_TRANSCRIPT
        default_hr_doc = ""
        default_hr_note = ""

    with st.expander("Candidate Interview Transcript & Resume Credentials", expanded=True):
        if is_automated_hr:
            st.caption("Status: Pending Screening Review (Unprocessed) — Locked automated stream from Google Meet.")

        hr_input_text = st.text_area(
            "Screening Interview Transcript (Google Meet / Read AI):",
            value=default_hr_text,
            height=180,
            disabled=is_automated_hr
        )
        hr_url_input = st.text_input(
            "Candidate LinkedIn / Resume URL (Optional):",
            value=default_hr_doc,
            placeholder="https://linkedin.com/in/candidate or resume URL"
        )
        if default_hr_note:
            st.caption(f"Verified Credentials: {default_hr_note}")

    col_hrl, col_hrbtn, col_hrr = st.columns([1, 2, 1])
    with col_hrbtn:
        run_hr = st.button("Grade Candidate Screening", type="primary", use_container_width=True)

    if run_hr:
        with st.spinner("Evaluating candidate qualifications and linguistic competence..."):
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

        # Metrics
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-card">
                <div class="kpi-label">Candidate Fit Score</div>
                <div class="kpi-value">{hr_out.overall_fit_score} <span style="font-size:0.9rem;">/ 100</span></div>
                <div class="kpi-sub">Overall Suitability Rating</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Bilingual Fluency</div>
                <div class="kpi-value" style="font-size:1.25rem; margin-top:0.35rem;">{hr_out.bilingual_fluency_rating}</div>
                <div class="kpi-sub">US Lending Communication</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Recommended Action</div>
                <div class="kpi-value" style="font-size:1.15rem; margin-top:0.4rem; color:#3EA258;">{hr_out.recommended_action}</div>
                <div class="kpi-sub">Recruiting Pipeline Next Step</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_hr_card, col_hr_guide = st.columns([1, 1])

        with col_hr_card:
            st.markdown("#### Candidate Assessment Summary")
            st.markdown(f"""
            <div class="studio-card">
                <div class="studio-card-header">
                    <span class="studio-card-title">{hr_out.candidate_name}</span>
                    <span class="nudesk-badge badge-green">{hr_out.applied_role}</span>
                </div>
                <p style="color:var(--nd-text); font-size:0.9rem; line-height:1.6;">{hr_out.executive_summary}</p>
                
                <h5 style="margin-top:1rem; margin-bottom:0.5rem; color:var(--nd-text);">Verified Technical Competencies:</h5>
            """, unsafe_allow_html=True)

            for comp in hr_out.technical_competencies:
                st.markdown(f"""
                <div class="bullet-item">
                    <span class="bullet-dot"></span>
                    <span class="bullet-text">{comp}</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        with col_hr_guide:
            st.markdown("#### Hiring Manager Case-Study Questions")
            st.markdown("""
            <div class="studio-card">
                <div class="studio-card-header">
                    <span class="studio-card-title">Next Round Interview Protocol</span>
                    <span class="nudesk-badge badge-navy">Technical Probe</span>
                </div>
            """, unsafe_allow_html=True)

            for idx, q in enumerate(hr_out.next_interview_focus_questions, 1):
                st.markdown(f"""
                <div style="background:var(--nd-surface-alt); border:1px solid var(--nd-border); border-radius:4px; padding:0.65rem 0.9rem; margin-bottom:0.5rem; font-size:0.88rem; color:var(--nd-text);">
                    <strong>Q{idx}:</strong> {q}
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # Operational Approval & Auto-Persistence
        col_hrapl, col_hrapbtn, col_hrapr = st.columns([1, 2, 1])
        with col_hrapbtn:
            if st.button("Advance Candidate & Log to Talent Tracker", type="primary", use_container_width=True):
                rec_id = database.save_operation(
                    operator_name=persona.name,
                    operator_role=persona.role_title,
                    module_type="hr",
                    entity_name=f"{hr_out.candidate_name} ({hr_out.applied_role})",
                    headline_metric=f"Score: {hr_out.overall_fit_score}/100 | {hr_out.bilingual_fluency_rating}",
                    assessment_summary=hr_out.executive_summary,
                    full_output_json=hr_out.model_dump(),
                    dispatch_status="Synced to HR Pipeline",
                    is_processed=1,
                    source_channel="Google Meet / Read AI"
                )
                st.session_state.hr_selected_inbox = None
                st.success(f"Audit Record #{rec_id} saved. Candidate file advanced to Hiring Manager queue.")
                st.rerun()

# =========================================================================
# TAB 4: EXECUTIVE KPI DASHBOARD & AUDIT HISTORY
# =========================================================================
with tabs[3]:
    st.markdown("### Executive Overview & Operational Audit Trail")
    st.markdown(f"Consolidated operations across Credit, Sales, and HR teams in Mazatlán ({time_window_choices[st.session_state.time_window]}).")

    # Global KPI Top Bar
    all_records = database.get_filtered_operations(
        module_filter="all",
        status_filter="all",
        time_window=st.session_state.time_window,
        limit=500
    )
    total_ops = len(all_records)
    pending_total = len([r for r in all_records if r["is_processed"] == 0])
    processed_total = len([r for r in all_records if r["is_processed"] == 1])

    credit_total = len([r for r in all_records if r["module_type"] == "credit"])
    sales_total = len([r for r in all_records if r["module_type"] == "sales"])
    hr_total = len([r for r in all_records if r["module_type"] == "hr"])

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

    # Multi-Filter Controls Row
    st.markdown("#### Operational Log")
    col_fmod, col_fstatus, col_fsearch = st.columns([2, 2, 3])
    with col_fmod:
        exec_mod_filter = st.selectbox(
            "Filter by Department:",
            ["All Modules", "Credit Operations", "Sales Outreach", "HR Talent"],
            index=0
        )
    with col_fstatus:
        exec_status_filter = st.selectbox(
            "Filter by Processing State:",
            ["All Records", "Pending Intake (Unprocessed)", "Processed / Synced"],
            index=0
        )
    with col_fsearch:
        exec_search_query = st.text_input(
            "Search Across All Records:",
            placeholder="Partial match on entity, metric, summary, or operator...",
            key="exec_kw_search"
        )

    col_fsort, col_forder, _ = st.columns([2, 2, 3])
    with col_fsort:
        exec_sort_by = st.selectbox(
            "Sort Records By:",
            ["Date / Time", "Entity Name", "Headline Metric", "Operator"],
            index=0
        )
    with col_forder:
        exec_sort_order = st.selectbox(
            "Order Direction:",
            ["Newest First (Descending)", "Oldest First (Ascending)"],
            index=0
        )

    # Translate filter params to database query
    mod_map = {
        "All Modules": "all",
        "Credit Operations": "credit",
        "Sales Outreach": "sales",
        "HR Talent": "hr"
    }
    status_map = {
        "All Records": "all",
        "Pending Intake (Unprocessed)": "pending",
        "Processed / Synced": "processed"
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
        time_window=st.session_state.time_window,
        limit=150
    )

    if filtered_exec_records:
        for rec in filtered_exec_records:
            mod_badge = "badge-navy" if rec["module_type"] == "credit" else ("badge-teal" if rec["module_type"] == "sales" else "badge-green")
            is_pend = (rec.get("is_processed", 1) == 0)
            status_badge_cls = "badge-teal" if is_pend else "badge-green"
            status_str = rec.get("dispatch_status", "Synced")
            time_str = rec.get("timestamp", "")
            entity_str = rec.get("entity_name", "")
            metric_str = rec.get("headline_metric", "")

            # Single-line card summary with expander
            exp_label = f"[{rec['module_type'].upper()}]   {entity_str}   |   {metric_str}   |   {time_str}"
            with st.expander(exp_label, expanded=False):
                st.markdown(f"""<div style="margin-bottom:0.6rem;">
<span class="nudesk-badge {mod_badge}">{rec['module_type'].upper()}</span>
<span class="nudesk-badge {status_badge_cls}" style="margin-left:0.4rem;">{status_str}</span>
<span style="font-size:0.85rem; color:#64748B; margin-left:0.75rem;">Source: {rec.get('source_channel', '')} &bull; Handled by: {rec.get('operator_name', '')} ({rec.get('operator_role', '')})</span>
</div>""", unsafe_allow_html=True)

                col_e1, col_e2 = st.columns([3, 2])
                with col_e1:
                    st.markdown("**Assessment Summary & Operational Notes:**")
                    st.write(rec.get("assessment_summary", ""))
                with col_e2:
                    st.markdown("**Structured JSON Output:**")
                    try:
                        st.json(json.loads(rec.get("full_output_json", "{}")))
                    except Exception:
                        st.text(rec.get("full_output_json", ""))
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
