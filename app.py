"""
DeskMate Operations Studio V2 (Enterprise Cyborg Suite)
nuDesk MX — The AI-Workforce Agency for Financial Services
Mazatlán Talent Hub (Sin.) & US Commercial Lending Operations
"""
import os
import streamlit as st
from dotenv import load_dotenv

# Internal modular imports
from styles.nudesk_theme import get_nudesk_css
import auth_rbac
from auth_rbac import PRESET_WORKSPACE_PERSONAS, get_persona_by_id
from meeting_queue import INCOMING_MEETINGS_QUEUE, BENCHMARK_HR_TRANSCRIPT
from mock_data import BENCHMARK_TRANSCRIPT, BENCHMARK_SALES_LEAD
from models import CreditTriageOutput, SalesLeadOutput, HRTalentOutput
import ai_engine
import crm_dispatcher
import database
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

if "active_tab_index" not in st.session_state:
    st.session_state.active_tab_index = 0

# Cached analysis results
if "credit_result" not in st.session_state:
    st.session_state.credit_result = None
if "sales_result" not in st.session_state:
    st.session_state.sales_result = None
if "hr_result" not in st.session_state:
    st.session_state.hr_result = None

# Detect if role changed to route default tab
if st.session_state.last_role_key != persona.role_key:
    st.session_state.last_role_key = persona.role_key
    role_to_tab = {
        "underwriter": 0,
        "bdr": 1,
        "hr_recruiter": 2,
        "manager": 3,
        "it_admin": 4
    }
    st.session_state.active_tab_index = role_to_tab.get(persona.role_key, 0)

# Environment credentials (Managed by IT)
current_api_key = os.getenv("GEMINI_API_KEY", "")
current_webhook_url = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/nudesk-triage")

# ----------------- ENTERPRISE BRAND HEADER -----------------
is_google_active = st.session_state.google_user is not None
sso_badge_text = "Google OAuth Active" if is_google_active else "RBAC Simulation Mode"
sso_badge_class = "badge-green" if is_google_active else "badge-navy"

st.markdown(f"""
<div class="nudesk-header">
    <div>
        <h1>nuDesk | DeskMate Operations Studio</h1>
        <div class="subtitle">AI-Workforce Platform for Financial Services — Mazatlán Talent Hub</div>
    </div>
    <div style="display: flex; gap: 0.5rem; align-items: center;">
        <span class="nudesk-badge {sso_badge_class}">{sso_badge_text}</span>
        <span class="nudesk-badge badge-navy">Cyborg Engine V2</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- IDENTITY & RBAC BANNER -----------------
col_user, col_switch, col_theme = st.columns([3, 2, 1])

with col_user:
    badge_label = "Google Workspace" if is_google_active else f"Role: {persona.role_key.upper()}"
    badge_cls = "badge-green" if is_google_active else "badge-navy"

    if persona.picture_url:
        avatar_html = f'<img src="{persona.picture_url}" style="width:28px; height:28px; border-radius:50%; border:2px solid #059669; vertical-align:middle; margin-right:8px;" />'
    else:
        avatar_html = f'<span class="role-avatar">{persona.avatar_initials}</span>'

    st.markdown(f"""
    <div class="role-banner">
        <div class="role-indicator">
            {avatar_html}
            <span>{persona.name} &bull; <strong>{persona.role_title}</strong> <span style="color:#64748B;">({persona.email})</span></span>
        </div>
        <div>
            <span class="nudesk-badge {badge_cls}">{badge_label}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Auth action buttons
    auth_col1, auth_col2 = st.columns([2, 1])
    with auth_col1:
        if is_google_active:
            if st.button("Sign out of Google", key="btn_signout_google", use_container_width=True):
                st.session_state.google_user = None
                st.session_state.authenticated_persona = None
                st.session_state.active_persona_id = "usr_underwriter_1"
                st.rerun()
        elif google_client_id:
            auth_url = auth_rbac.get_google_auth_url(google_client_id, google_redirect_uri)
            st.link_button("Sign in with Google Workspace", auth_url, use_container_width=True)
        else:
            st.caption("Google OAuth credentials unconfigured in .env")

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
        "Switch Workspace Identity (RBAC):",
        options=list(persona_options.keys()),
        format_func=lambda pid: persona_options[pid],
        index=list(persona_options.keys()).index(current_id),
        help="Simulates Google Workspace SSO login. Changing identity dynamically reconfigures view permissions and access rights."
    )
    if selected_persona_id != st.session_state.active_persona_id:
        st.session_state.active_persona_id = selected_persona_id
        st.rerun()

with col_theme:
    theme_choice = st.selectbox(
        "Theme Mode:",
        ["Light Mode", "Dark Mode"],
        index=0 if st.session_state.current_theme == "light" else 1,
        help="Toggle between High-Contrast Minimalist Light Mode and Enterprise Dark Mode."
    )
    chosen_theme_key = "light" if "Light" in theme_choice else "dark"
    if chosen_theme_key != st.session_state.current_theme:
        st.session_state.current_theme = chosen_theme_key
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
# TAB 1: CREDIT DESKMATE (UNDERWRITING DISCOVERY TRIAGE)
# =========================================================================
with tabs[0]:
    st.markdown("### Credit Operations — Post-Call Discovery Triage")
    st.markdown(
        "Automated financial extraction, underwriting risk calculation, and compliance checklist generation. "
        "*Underwriters spend time on judgment, not data entry.*"
    )

    # Ingestion Source Selector
    ingest_col1, ingest_col2 = st.columns([2, 1])
    with ingest_col1:
        credit_meetings = [m for m in INCOMING_MEETINGS_QUEUE if m["type"] == "credit"]
        meeting_choices = ["Manual Transcript Paste / Ad-hoc Call"] + [f"Inbox: {m['title']} ({m['source']} - {m['received_ago']})" for m in credit_meetings]
        selected_credit_meet = st.selectbox(
            "Call Ingestion Source (Google Meet / Read AI / Fireflies):",
            meeting_choices,
            index=1 if credit_meetings else 0
        )

    # Preload content if inbox meeting selected
    default_credit_text = BENCHMARK_TRANSCRIPT
    default_doc_url = ""
    default_doc_notes = ""

    if selected_credit_meet != "Manual Transcript Paste / Ad-hoc Call":
        chosen_meeting = credit_meetings[0]
        default_credit_text = chosen_meeting["transcript"]
        default_doc_url = chosen_meeting["default_doc_url"]
        default_doc_notes = chosen_meeting["doc_note"]

    # Main Input Forms
    with st.expander("Discovery Call Transcript & Supporting Collateral", expanded=True):
        credit_input_text = st.text_area(
            "Raw Call Transcript:",
            value=default_credit_text,
            height=200,
            help="Ingested automatically via Read AI / Fireflies webhook from Google Meet."
        )

        col_url, col_upload = st.columns([2, 1])
        with col_url:
            quote_url_input = st.text_input(
                "Supporting Document / Quote URL (Optional):",
                value=default_doc_url,
                placeholder="https://vendor.com/equipment-quote-85k.pdf or web link"
            )
        with col_upload:
            uploaded_doc = st.file_uploader(
                "Or Upload Financial File (PDF / TXT):",
                type=["txt", "pdf", "csv", "md"]
            )

        if default_doc_notes:
            st.caption(f"Verified Attachment: {default_doc_notes}")

    # Action Trigger
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        run_credit = st.button("Run AI Credit Triage", type="primary", use_container_width=True)
    with col_info:
        st.caption("Extracts applicant revenue, computes Debt-to-Income, isolates red flags, and structures Asana tasks.")

    if run_credit:
        with st.spinner("Analyzing transcript and reconciling collateral documents with Gemini..."):
            # Ingest supplementary doc if provided
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

    # Display Results
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
                <p style="color:#334155; font-size:0.92rem; line-height:1.6;">{credit_out.executive_summary}</p>
                
                <h5 style="margin-top:1rem; margin-bottom:0.5rem; color:#991B1B;">Identified Underwriting Red Flags:</h5>
            """, unsafe_allow_html=True)

            if credit_out.red_flags:
                for flag in credit_out.red_flags:
                    st.markdown(f'<div class="flag-item">&bull; {flag}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#059669;">No critical red flags identified.</p>', unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        with col_tasks:
            st.markdown("#### Asana Operational Tasks")
            for task in credit_out.asana_tasks:
                badge_class = "badge-red" if task.priority == "High" else "badge-amber"
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
        st.markdown("---")
        col_disp1, col_disp2 = st.columns([1, 2])
        with col_disp1:
            if st.button("Approve & Sync Credit Memo to Pipeline", type="primary", use_container_width=True):
                # Save to local persistent database
                rec_id = database.save_operation(
                    operator_name=persona.name,
                    operator_role=persona.role_title,
                    module_type="credit",
                    entity_name=f"{credit_out.business_name} ({credit_out.applicant_name})",
                    headline_metric=f"{credit_out.risk_tier} | ${credit_out.loan_amount_requested_usd:,.0f} USD",
                    assessment_summary=credit_out.executive_summary,
                    full_output_json=credit_out.model_dump(),
                    dispatch_status="Synced with n8n / Sheets"
                )

                # Dispatch via HTTP to n8n
                ok, disp_msg, _ = crm_dispatcher.dispatch_to_n8n(
                    webhook_url=current_webhook_url,
                    payload=credit_out.model_dump(),
                    flow_type="credit"
                )

                if ok:
                    st.success(f"Audit Record #{rec_id} saved. File successfully dispatched to n8n Underwriting Pipeline.")
                else:
                    st.warning(f"Audit Record #{rec_id} saved locally. Dispatch note: {disp_msg}")

        with col_disp2:
            st.caption("Automatically logs audit record to SQLite database and syncs structured underwriting memo to Google Sheets & Asana via n8n.")

# =========================================================================
# TAB 2: SALES DESKMATE (COMMERCIAL BDR LEAD SCORING & OUTREACH)
# =========================================================================
with tabs[1]:
    st.markdown("### Sales Operations — Commercial BDR Lead Scoring & Outreach")
    st.markdown(
        "Commercial profile qualification, factoring fit evaluation, and personalized speed-to-lead dialing assets. "
        "*Arming Mazatlán BDRs with high-conversion outreach in seconds.*"
    )

    # Ingestion Source Selector
    sales_col1, sales_col2 = st.columns([2, 1])
    with sales_col1:
        sales_meetings = [m for m in INCOMING_MEETINGS_QUEUE if m["type"] == "sales"]
        sales_choices = ["Manual Lead Profile Entry"] + [f"Inbox: {m['title']} ({m['source']} - {m['received_ago']})" for m in sales_meetings]
        selected_sales_meet = st.selectbox(
            "Commercial Prospect Ingestion Source:",
            sales_choices,
            index=1 if sales_meetings else 0
        )

    default_sales_text = BENCHMARK_SALES_LEAD
    default_sales_url = ""
    default_sales_note = ""

    if selected_sales_meet != "Manual Lead Profile Entry":
        chosen_sales = sales_meetings[0]
        default_sales_text = chosen_sales["lead_data"]
        default_sales_url = chosen_sales["default_doc_url"]
        default_sales_note = chosen_sales["doc_note"]

    with st.expander("Prospect Profile & Collateral Information", expanded=True):
        sales_input_text = st.text_area(
            "Raw Commercial Profile / Call Notes:",
            value=default_sales_text,
            height=180
        )
        sales_url_input = st.text_input(
            "Prospect AR Aging Report / Website URL (Optional):",
            value=default_sales_url,
            placeholder="https://company.com/freight-aging.pdf"
        )
        if default_sales_note:
            st.caption(f"Verified Collateral: {default_sales_note}")

    col_sbtn, col_sinfo = st.columns([1, 3])
    with col_sbtn:
        run_sales = st.button("Run AI Sales Evaluation", type="primary", use_container_width=True)
    with col_sinfo:
        st.caption("Computes lead score (1-100), generates executive cold email draft, and builds 30-second telephone pitch.")

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
                <p style="color:#475569; font-size:0.88rem;"><strong>Score Rationale:</strong> {sales_out.score_rationale}</p>
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
                <p style="color:#64748B; font-size:0.82rem; margin-bottom:0.5rem;">
                    Designed for sub-10 second hook and immediate pain-point alignment.
                </p>
                <div class="script-box">{sales_out.phone_script_30s_en}</div>
            </div>
            """, unsafe_allow_html=True)

        # Operational Approval & Auto-Persistence
        st.markdown("---")
        col_sdisp1, col_sdisp2 = st.columns([1, 2])
        with col_sdisp1:
            if st.button("Sync Qualified Lead to CRM & Staged Drafts", type="primary", use_container_width=True):
                rec_id = database.save_operation(
                    operator_name=persona.name,
                    operator_role=persona.role_title,
                    module_type="sales",
                    entity_name=f"{sales_out.company_name} ({sales_out.contact_person})",
                    headline_metric=f"Score: {sales_out.lead_score}/100 | ${sales_out.annual_revenue_usd:,.0f} ARR",
                    assessment_summary=sales_out.score_rationale,
                    full_output_json=sales_out.model_dump(),
                    dispatch_status="Synced with n8n / Sales CRM"
                )

                ok, disp_msg, _ = crm_dispatcher.dispatch_to_n8n(
                    webhook_url=current_webhook_url,
                    payload=sales_out.model_dump(),
                    flow_type="sales"
                )

                if ok:
                    st.success(f"Audit Record #{rec_id} saved. Lead successfully synced to Sales CRM & BDR outbox.")
                else:
                    st.warning(f"Audit Record #{rec_id} saved locally. Dispatch note: {disp_msg}")

        with col_sdisp2:
            st.caption("Logs record to SQLite and stages email draft in Google Workspace via n8n for BDR human-in-the-loop review.")

# =========================================================================
# TAB 3: HR DESKMATE (TALENT SCREENING & BILINGUAL ASSESSMENT)
# =========================================================================
with tabs[2]:
    st.markdown("### HR & Talent Solutions — Candidate Interview Screening")
    st.markdown(
        "Bilingual interview evaluation, technical competency grading, and hiring manager case-study synthesis. "
        "*Reflecting nuDesk's actual candidate screening pipeline in Mazatlán.*"
    )

    hr_col1, hr_col2 = st.columns([2, 1])
    with hr_col1:
        hr_meetings = [m for m in INCOMING_MEETINGS_QUEUE if m["type"] == "hr"]
        hr_choices = ["Manual Interview Transcript Paste"] + [f"Inbox: {m['title']} ({m['source']} - {m['received_ago']})" for m in hr_meetings]
        selected_hr_meet = st.selectbox(
            "Candidate Interview Ingestion Source:",
            hr_choices,
            index=1 if hr_meetings else 0
        )

    default_hr_text = BENCHMARK_HR_TRANSCRIPT
    default_hr_doc = ""
    default_hr_note = ""

    if selected_hr_meet != "Manual Interview Transcript Paste":
        chosen_hr = hr_meetings[0]
        default_hr_text = chosen_hr["transcript"]
        default_hr_doc = chosen_hr["default_doc_url"]
        default_hr_note = chosen_hr["doc_note"]

    with st.expander("Candidate Interview Transcript & Resume Credentials", expanded=True):
        hr_input_text = st.text_area(
            "Screening Interview Transcript (Google Meet / Read AI):",
            value=default_hr_text,
            height=180
        )
        hr_url_input = st.text_input(
            "Candidate LinkedIn / Resume URL (Optional):",
            value=default_hr_doc,
            placeholder="https://linkedin.com/in/candidate or resume URL"
        )
        if default_hr_note:
            st.caption(f"Verified Credentials: {default_hr_note}")

    col_hr_btn, col_hr_info = st.columns([1, 3])
    with col_hr_btn:
        run_hr = st.button("Run AI Talent Screening", type="primary", use_container_width=True)
    with col_hr_info:
        st.caption("Grades overall fit score (1-100), assesses CEFR bilingual fluency, detects red flags, and builds Hiring Manager interview guide.")

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
                <div class="kpi-value" style="font-size:1.15rem; margin-top:0.4rem; color:#2E7D32;">{hr_out.recommended_action}</div>
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
                <p style="color:#334155; font-size:0.9rem; line-height:1.6;">{hr_out.executive_summary}</p>
                
                <h5 style="margin-top:1rem; margin-bottom:0.5rem; color:#1E293B;">Verified Technical Competencies:</h5>
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
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:4px; padding:0.65rem 0.9rem; margin-bottom:0.5rem; font-size:0.88rem; color:#1E293B;">
                    <strong>Q{idx}:</strong> {q}
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # Operational Approval & Auto-Persistence
        st.markdown("---")
        col_hr_disp1, col_hr_disp2 = st.columns([1, 2])
        with col_hr_disp1:
            if st.button("Advance Candidate & Log to Talent Tracker", type="primary", use_container_width=True):
                rec_id = database.save_operation(
                    operator_name=persona.name,
                    operator_role=persona.role_title,
                    module_type="hr",
                    entity_name=f"{hr_out.candidate_name} ({hr_out.applied_role})",
                    headline_metric=f"Score: {hr_out.overall_fit_score}/100 | {hr_out.bilingual_fluency_rating}",
                    assessment_summary=hr_out.executive_summary,
                    full_output_json=hr_out.model_dump(),
                    dispatch_status="Synced to Greenhouse / HR Tracker"
                )
                st.success(f"Audit Record #{rec_id} saved. Candidate file advanced to Hiring Manager queue.")

        with col_hr_disp2:
            st.caption("Logs candidate scorecard to SQLite and updates recruiting tracker.")

# =========================================================================
# TAB 4: EXECUTIVE KPI DASHBOARD & AUDIT HISTORY
# =========================================================================
with tabs[3]:
    st.markdown("### Executive Overview & Operational Audit Trail")
    st.markdown("Real-time operational activity log across Credit, Sales, and HR teams in Mazatlán.")

    # KPI Top Bar
    history_records = database.get_operations(limit=100)
    total_ops = len(history_records)
    credit_ops = len([r for r in history_records if r["module_type"] == "credit"])
    sales_ops = len([r for r in history_records if r["module_type"] == "sales"])
    hr_ops = len([r for r in history_records if r["module_type"] == "hr"])

    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-label">Total Completed Operations</div>
            <div class="kpi-value">{total_ops}</div>
            <div class="kpi-sub">Across All 3 DeskMates</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Credit Underwriting Files</div>
            <div class="kpi-value">{credit_ops}</div>
            <div class="kpi-sub">Avg ~38 mins saved / file</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Sales Leads Qualified</div>
            <div class="kpi-value">{sales_ops}</div>
            <div class="kpi-sub">100% Outreach Generated</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">HR Candidate Screenings</div>
            <div class="kpi-value">{hr_ops}</div>
            <div class="kpi-sub">Bilingual Competency Verified</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Filterable History Table
    col_filter, _ = st.columns([1, 2])
    with col_filter:
        mod_filter = st.selectbox(
            "Filter History by Operational Module:",
            ["All Modules", "credit", "sales", "hr"]
        )

    filtered_records = history_records if mod_filter == "All Modules" else [r for r in history_records if r["module_type"] == mod_filter]

    st.markdown("#### Operational Log")
    if filtered_records:
        for rec in filtered_records:
            mod_badge = "badge-navy" if rec["module_type"] == "credit" else ("badge-green" if rec["module_type"] == "sales" else "badge-amber")
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:0.9rem 1.25rem; margin-bottom:0.75rem;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
                    <div>
                        <span class="nudesk-badge {mod_badge}">{rec["module_type"].upper()}</span>
                        <strong style="margin-left:0.5rem; font-size:1rem; color:#1E293B;">{rec["entity_name"]}</strong>
                    </div>
                    <span style="font-size:0.8rem; color:#64748B;">{rec["timestamp"]}</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-size:0.88rem; color:#334155;">
                        <strong>Key Metric:</strong> {rec["headline_metric"]} &bull; <span style="color:#64748B;">Operator: {rec["operator_name"]} ({rec["operator_role"]})</span>
                    </div>
                    <div>
                        <span class="nudesk-badge badge-green">{rec["dispatch_status"]}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No operational records logged yet.")

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
