import os
import json
import streamlit as st
from dotenv import load_dotenv

from models import CreditTriageOutput, SalesLeadOutput
from mock_data import MOCK_FIREFLIES_TRANSCRIPT, MOCK_SALES_LEAD_RAW
from ai_engine import analyze_credit_call, qualify_sales_lead
from crm_dispatcher import dispatch_to_n8n

load_dotenv()

# Page configuration (No emojis per global styling rules)
st.set_page_config(
    page_title="nuDesk Operations Studio | nuDesk MX",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 5px solid #1E3A8A;
        margin-bottom: 1rem;
    }
    .risk-high {
        color: #DC2626;
        font-weight: 700;
    }
    .risk-moderate {
        color: #D97706;
        font-weight: 700;
    }
    .risk-low {
        color: #059669;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR CONFIGURATION -----------------
with st.sidebar:
    st.markdown("### nuDesk MX | Operations Hub")
    st.markdown("**Cyborg Workforce System (Mazatlan, Sin.)**")
    st.markdown("---")

    default_api_key = os.getenv("GEMINI_API_KEY", "")
    api_key_input = st.text_input(
        "Google Gemini API Key:",
        value=default_api_key,
        type="password",
        help="Free key from https://aistudio.google.com/. If left blank, app operates in Demonstration Mode."
    )

    default_n8n_url = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/nudesk-triage")
    n8n_url_input = st.text_input(
        "n8n Webhook Endpoint:",
        value=default_n8n_url,
        help="Local or remote n8n webhook URL. Defaults to local Docker container."
    )

    # Operational status indicator
    if api_key_input and api_key_input.strip():
        st.success("[STATUS] Live AI Engine Active (Cost-Optimized: Gemini 3.5 Flash-Lite)")
        st.caption("Prioritizing gemini-3.5-flash-lite for maximum cost efficiency and speed, with automatic cascade on demand spikes.")
    else:
        st.warning(
            "[STATUS] Demonstration Mode Active (Precomputed Data)\n\n"
            "This prototype is currently running with realistic synthetic benchmarks. "
            "To execute live inference with custom inputs, enter your free Gemini API key above."
        )

    st.markdown("---")
    st.markdown("#### About nuDesk FinServ Engine")
    st.caption(
        "Bilingual nearshore operations combining human expertise in Mazatlan with autonomous "
        "nuDesk AI agents to double underwriting and sales productivity for US commercial lenders."
    )
    st.markdown("---")
    st.markdown("[Get Free Google AI Studio Key](https://aistudio.google.com/)")

# ----------------- SESSION STATE MANAGEMENT -----------------
if "credit_output" not in st.session_state:
    st.session_state.credit_output = None
if "credit_is_fallback" not in st.session_state:
    st.session_state.credit_is_fallback = False
if "credit_msg" not in st.session_state:
    st.session_state.credit_msg = ""

if "sales_output" not in st.session_state:
    st.session_state.sales_output = None
if "sales_is_fallback" not in st.session_state:
    st.session_state.sales_is_fallback = False
if "sales_msg" not in st.session_state:
    st.session_state.sales_msg = ""

if "transcript_text" not in st.session_state:
    st.session_state.transcript_text = ""

if "sales_input_text" not in st.session_state:
    st.session_state.sales_input_text = ""

# ----------------- MAIN INTERFACE -----------------
st.markdown('<div class="main-header">nuDesk Operations Studio</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    'Autonomous Post-Call Discovery Triage, Asana Task Generation, and Hyper-Personalized Sales Outreach Engine'
    '</div>',
    unsafe_allow_html=True
)

tab_credit, tab_sales, tab_architecture = st.tabs([
    "Credit Operations (Fireflies Triage)",
    "Sales Operations (Lead Qualifier & Outreach)",
    "System Architecture & n8n Blueprint"
])

# ================= TAB 1: CREDIT OPERATIONS =================
with tab_credit:
    st.subheader("Post-Call Credit Triage & Underwriting Memo")
    st.markdown(
        "Ingests unstructured discovery transcripts from dialers/Fireflies, extracts borrower financials, "
        "determines credit risk tier, detects red flags, and compiles operational tasks for underwriting."
    )

    col_btn_load, col_btn_clear = st.columns([1, 4])
    with col_btn_load:
        if st.button("Load Demo Transcript (Dallas, TX Fleet)"):
            st.session_state.transcript_text = MOCK_FIREFLIES_TRANSCRIPT
    with col_btn_clear:
        if st.button("Clear Input", key="clear_credit"):
            st.session_state.transcript_text = ""
            st.session_state.credit_output = None

    transcript_area = st.text_area(
        "Call Transcript (Raw Dialog):",
        value=st.session_state.transcript_text,
        height=200,
        placeholder="Paste customer call transcript from Fireflies.ai, Gong, or phone recordings..."
    )
    st.session_state.transcript_text = transcript_area

    if st.button("Execute Credit Analysis with nuDesk AI", type="primary"):
        if not transcript_area.strip():
            st.warning("Please provide a call transcript or click 'Load Demo Transcript' to proceed.")
        else:
            with st.spinner("Processing call transcript and extracting credit parameters..."):
                output, is_fallback, err_msg = analyze_credit_call(
                    transcript_area,
                    api_key=api_key_input
                )
                st.session_state.credit_output = output
                st.session_state.credit_is_fallback = is_fallback
                st.session_state.credit_msg = err_msg or ""

    # Display Credit Triage Results
    if st.session_state.credit_output:
        cred: CreditTriageOutput = st.session_state.credit_output
        st.markdown("---")
        st.markdown("### Structured Underwriting Memo")

        if st.session_state.credit_is_fallback:
            st.warning(
                "**[DEMONSTRATION MODE NOTICE]**: This underwriting memo is displaying pre-computed benchmark data. "
                "For live AI extraction on dynamic or novel transcripts, please enter a valid Google Gemini API key in the sidebar."
            )
        else:
            notice = st.session_state.credit_msg if st.session_state.credit_msg else "Generated in real time by Google Gemini."
            st.success(
                f"**[LIVE INFERENCE NOTICE]**: {notice} (Validated with strict Pydantic JSON schemas)."
            )

        # Top metric row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Applicant / Business", cred.business_name, cred.applicant_name)
        m2.metric("Requested Capital", f"${cred.loan_amount_requested_usd:,.2f} USD")
        m3.metric("Monthly Revenue", f"${cred.stated_monthly_revenue_usd:,.2f} USD")
        m4.metric("Estimated DTI", f"{cred.estimated_dti_ratio * 100:.1f}%")

        # Risk indicator banner
        risk_class = "risk-low" if cred.risk_tier == "Low Risk" else (
            "risk-moderate" if cred.risk_tier == "Moderate Risk" else "risk-high"
        )
        st.markdown(
            f"**Underwriting Assessment:** <span class='{risk_class}'>[{cred.risk_tier.upper()}]</span>",
            unsafe_allow_html=True
        )

        col_exec, col_flags = st.columns([1.2, 1.0])
        with col_exec:
            st.markdown("#### Executive Summary")
            st.info(cred.executive_summary)
            st.markdown(f"**Industry Sector:** {cred.industry}")

        with col_flags:
            st.markdown("#### Identified Red Flags & Underwriting Risks")
            if cred.red_flags:
                for idx, flag in enumerate(cred.red_flags, 1):
                    st.markdown(f"- **Risk {idx}:** {flag}")
            else:
                st.success("No critical red flags detected in call disclosures.")

        # Asana Operational Tasks
        st.markdown("#### Operational Tasks for Mazatlan Underwriting Team (Asana Sync)")
        task_data = [
            {
                "Task Title": t.task_title,
                "Priority": t.priority,
                "Assigned Role": t.assignee_role
            }
            for t in cred.asana_tasks
        ]
        st.table(task_data)

        # Dispatch section
        st.markdown("---")
        col_disp, col_preview = st.columns([1.5, 2.5])
        with col_disp:
            if st.button("Dispatch Credit File to n8n / Underwriting Pipeline", type="secondary"):
                success, msg, enriched_data = dispatch_to_n8n(
                    webhook_url=n8n_url_input,
                    payload=cred.model_dump(),
                    flow_type="credit"
                )
                if success:
                    st.success(f"[SUCCESS] {msg}")
                else:
                    st.error(f"[ERROR] {msg}")

        with col_preview:
            with st.expander("View JSON Payload for Webhook Transmission"):
                st.json(cred.model_dump())


# ================= TAB 2: SALES OPERATIONS =================
with tab_sales:
    st.subheader("Commercial Lead Qualifier & High-Conversion Outreach")
    st.markdown(
        "Scores inbound or scraped business prospects (1-100), analyzes financial fit for lending/factoring, "
        "and auto-generates persuasive cold email drafts and a 30-second telephone pitch in professional US English."
    )

    col_s_load, col_s_clear = st.columns([1, 4])
    with col_s_load:
        if st.button("Load Demo Commercial Prospect (Sunbelt Logistics)"):
            st.session_state.sales_input_text = MOCK_SALES_LEAD_RAW
    with col_s_clear:
        if st.button("Clear Input", key="clear_sales"):
            st.session_state.sales_input_text = ""
            st.session_state.sales_output = None

    lead_text_area = st.text_area(
        "Commercial Prospect Parameters:",
        value=st.session_state.sales_input_text,
        height=180,
        placeholder="Enter company profile, revenue, fleet size, working capital challenges, or commercial intent..."
    )
    st.session_state.sales_input_text = lead_text_area

    if st.button("Qualify Lead and Generate Outreach", type="primary"):
        if not lead_text_area.strip():
            st.warning("Please provide commercial prospect data or click 'Load Demo Commercial Prospect'.")
        else:
            with st.spinner("Scoring prospect and engineering personalized BDR outreach..."):
                sales_res, is_fallback, err_msg = qualify_sales_lead(
                    lead_text_area,
                    api_key=api_key_input
                )
                st.session_state.sales_output = sales_res
                st.session_state.sales_is_fallback = is_fallback
                st.session_state.sales_msg = err_msg or ""

    # Display Sales Results
    if st.session_state.sales_output:
        sale: SalesLeadOutput = st.session_state.sales_output
        st.markdown("---")
        st.markdown("### Qualification Results & BDR Toolkit")

        if st.session_state.sales_is_fallback:
            st.warning(
                "**[DEMONSTRATION MODE NOTICE]**: This sales qualification and outreach pack is displaying pre-computed benchmark data. "
                "For live AI scoring on dynamic or novel prospects, please enter a valid Google Gemini API key in the sidebar."
            )
        else:
            notice = st.session_state.sales_msg if st.session_state.sales_msg else "Generated in real time by Google Gemini."
            st.success(
                f"**[LIVE INFERENCE NOTICE]**: {notice} (Validated with strict Pydantic JSON schemas)."
            )

        s1, s2, s3 = st.columns([1.2, 1.5, 1.3])
        s1.metric("Lead Score", f"{sale.lead_score} / 100")
        s2.metric("Target Company", sale.company_name, sale.contact_person)
        s3.metric("Annual Revenue", f"${sale.annual_revenue_usd:,.2f} USD")

        st.progress(sale.lead_score / 100.0)
        st.markdown(f"**Score Rationale:** {sale.score_rationale}")

        col_email, col_phone = st.columns(2)

        with col_email:
            st.markdown("#### Hyper-Personalized Cold Email (US Business English)")
            st.text_area("Cold Email Draft (Ready to Send via Gmail / Outreach):", value=sale.cold_email_en, height=260)

        with col_phone:
            st.markdown("#### 30-Second Cold Calling Phone Script (Mazatlan BDRs)")
            st.text_area("Verbal Phone Script (Speed-to-Lead Dialing):", value=sale.phone_script_30s_en, height=260)

        # Dispatch section
        st.markdown("---")
        col_s_disp, col_s_preview = st.columns([1.5, 2.5])
        with col_s_disp:
            if st.button("Dispatch Qualified Lead to n8n / Sales CRM", type="secondary"):
                success, msg, enriched_data = dispatch_to_n8n(
                    webhook_url=n8n_url_input,
                    payload=sale.model_dump(),
                    flow_type="sales"
                )
                if success:
                    st.success(f"[SUCCESS] {msg}")
                else:
                    st.error(f"[ERROR] {msg}")

        with col_s_preview:
            with st.expander("View JSON Payload for CRM Integration"):
                st.json(sale.model_dump())


# ================= TAB 3: ARCHITECTURE & BLUEPRINT =================
with tab_architecture:
    st.subheader("System Architecture & Enterprise Integration Flow")
    st.markdown(
        "Demonstrates the model-agnostic, event-driven decoupling between the AI inference layer, "
        "the local orchestration engine (n8n in Docker), and corporate endpoints (Google Sheets / Asana / CRMs)."
    )

    st.code("""
+-----------------------------------------------------------------------------------+
|                           nuDesk Operations Studio                                |
|                           (Streamlit Front-End)                                   |
+-----------------------------------------------------------------------------------+
           |                                                       |
           | 1. Raw Call Transcript / Lead Info                    | 3. Dispatch JSON
           v                                                       v
+------------------------------------+             +--------------------------------+
|       ai_engine.py                 |             |       crm_dispatcher.py        |
|  - Google Gemini 1.5 Flash         |             |  - HTTP POST with retry logic  |
|  - Pydantic Structured Outputs     |             |  - Simulation Mode Fallback    |
|  - Model-Agnostic Schema Guards    |             +--------------------------------+
+------------------------------------+                             |
           |                                                       | 4. Webhook Trigger
           v 2. Validated Schema Instances                         v
+-----------------------------------------------------------------------------------+
|                        Local Orchestrator: n8n (Docker)                           |
|       Endpoint: http://localhost:5678/webhook/nudesk-triage                       |
+-----------------------------------------------------------------------------------+
           |                                                       |
           | Branch A: Credit Operations                           | Branch B: Sales Operations
           v                                                       v
+------------------------------------+             +--------------------------------+
|  - Underwriting Google Sheet Row   |             |  - Sales Pipeline CRM Update   |
|  - Asana Task Creation via API     |             |  - Gmail Outbox Draft Staging  |
+------------------------------------+             +--------------------------------+
""", language="text")

    st.markdown("#### Quickstart: Running Local n8n in Docker")
    st.markdown("To start the local n8n instance with persistent data storage:")
    st.code("docker compose up -d", language="bash")
    st.markdown("Access the n8n visual editor at: `http://localhost:5678/`")

    with open("n8n_workflow_blueprint.json", "r") as f:
        blueprint_content = f.read()

    st.download_button(
        label="Download n8n Workflow Blueprint JSON",
        data=blueprint_content,
        file_name="n8n_workflow_blueprint.json",
        mime="application/json"
    )
    st.caption("Import this JSON directly into your n8n workspace via 'Import from File'.")
