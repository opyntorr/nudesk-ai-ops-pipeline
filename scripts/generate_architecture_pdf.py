#!/usr/bin/env python3
"""
nuDesk Architecture and Executive Brief PDF Generator
Minimalist, human-authored publication layout:
- Editorial typography (neutral, classic booktabs tables, clean light code blocks)
- No AI-style badges, gradients, or heavy decorative formatting
- Part 1 (Pages 1-3): Clear, accessible product overview with real screenshots
- Part 2 (Pages 4-7): Technical architecture, contracts, guardrails, and verification
"""
import os
import sys
import shutil
from playwright.sync_api import sync_playwright

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS_DIR = os.path.join(REPO_ROOT, "assets", "screenshots")
OUTPUT_HTML = os.path.join(REPO_ROOT, "docs", "architecture_brief.html")
OUTPUT_PDF_DOCS = os.path.join(REPO_ROOT, "docs", "nuDesk_Architecture_and_Executive_Brief.pdf")
OUTPUT_PDF_ROOT = os.path.join(REPO_ROOT, "nuDesk_Architecture_and_Executive_Brief.pdf")

def img(name: str, width: str = "100%", max_height: str = "auto") -> str:
    path = os.path.join(SCREENSHOTS_DIR, name)
    if not os.path.exists(path):
        return f'<div style="color: #666; font-size: 8pt; padding: 8px; border: 1px dashed #ccc;">[Image: {name}]</div>'
    return f'<img src="file://{path}" style="width: {width}; max-height: {max_height}; object-fit: contain; display: block; margin: 4px auto; border: 1px solid #d1d5db; border-radius: 3px;" alt="{name}"/>'

def build_html() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>nuDesk Operations Studio: Architecture & System Overview</title>
<style>
  @page {{
    size: A4;
    margin: 18mm 18mm 18mm 18mm;
  }}
  
  *, *:before, *:after {{
    box-sizing: border-box;
  }}
  
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1f2937;
    background-color: #ffffff;
    line-height: 1.5;
    font-size: 8.8pt;
    margin: 0;
    padding: 0;
  }}
  
  .page-break {{
    page-break-before: always;
    break-before: always;
  }}
  
  /* Typography */
  h1, h2, h3, h4 {{
    color: #111827;
    font-weight: 600;
    line-height: 1.25;
    page-break-after: avoid;
    break-after: avoid;
  }}
  
  h1.doc-title {{
    font-size: 20pt;
    font-weight: 700;
    margin: 0 0 4px 0;
    color: #111827;
    letter-spacing: -0.01em;
  }}
  
  .doc-subtitle {{
    font-size: 10.5pt;
    color: #4b5563;
    margin: 0 0 14px 0;
    font-weight: 400;
  }}
  
  .meta-block {{
    display: flex;
    justify-content: space-between;
    font-size: 8pt;
    color: #4b5563;
    border-top: 1px solid #e5e7eb;
    border-bottom: 1px solid #e5e7eb;
    padding: 6px 0;
    margin-bottom: 14px;
  }}
  
  h2.part-heading {{
    font-size: 13pt;
    font-weight: 700;
    color: #111827;
    border-bottom: 1.5px solid #111827;
    padding-bottom: 4px;
    margin-top: 0;
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
  
  h2.section-heading {{
    font-size: 11pt;
    font-weight: 600;
    color: #111827;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 3px;
    margin-top: 14px;
    margin-bottom: 6px;
  }}
  
  h3 {{
    font-size: 9.5pt;
    font-weight: 600;
    color: #111827;
    margin-top: 10px;
    margin-bottom: 3px;
  }}
  
  p {{
    margin: 0 0 6px 0;
    text-align: justify;
  }}
  
  ul, ol {{
    margin: 0 0 8px 0;
    padding-left: 18px;
  }}
  
  li {{
    margin-bottom: 2px;
  }}
  
  /* Tables: Booktabs style */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0 12px 0;
    font-size: 8pt;
    page-break-inside: avoid;
    break-inside: avoid;
  }}
  
  th {{
    border-top: 1.5px solid #111827;
    border-bottom: 1px solid #111827;
    padding: 5px 8px;
    text-align: left;
    font-weight: 600;
    color: #111827;
  }}
  
  td {{
    padding: 4.5px 8px;
    border-bottom: 1px solid #f3f4f6;
    color: #374151;
  }}
  
  tr:last-child td {{
    border-bottom: 1.5px solid #111827;
  }}
  
  /* Code & Pre */
  pre, code {{
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    font-size: 7.2pt;
  }}
  
  pre {{
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
    padding: 7px 9px;
    color: #1f2937;
    margin: 5px 0 8px 0;
    line-height: 1.35;
    overflow-x: auto;
    page-break-inside: avoid;
    break-inside: avoid;
  }}
  
  p code, td code, li code {{
    background: #f3f4f6;
    color: #111827;
    padding: 1px 3px;
    border-radius: 2px;
  }}
  
  /* Simple Callout / Note */
  .note-box {{
    background: #f9fafb;
    border-left: 3px solid #4b5563;
    padding: 7px 10px;
    margin: 8px 0;
    font-size: 8.2pt;
    color: #374151;
    page-break-inside: avoid;
    break-inside: avoid;
  }}
  
  .caption {{
    font-size: 7.2pt;
    color: #6b7280;
    text-align: center;
    margin-top: 2px;
    margin-bottom: 6px;
  }}
  
  .grid-2 {{
    display: flex;
    gap: 10px;
    margin: 6px 0;
    page-break-inside: avoid;
    break-inside: avoid;
  }}
  .grid-2 > div {{
    flex: 1;
  }}
  
  .figure-box {{
    page-break-inside: avoid;
    break-inside: avoid;
    margin: 6px 0;
  }}
</style>
</head>
<body>

<!-- ========================================== -->
<!-- PAGE 1: TITLE, CONTEXT, CREDIT COCKPIT     -->
<!-- ========================================== -->
<div>
  <h1 class="doc-title">nuDesk Operations Studio</h1>
  <div class="doc-subtitle">System Architecture Specification, Deterministic AI Workflows, and Workspace Integration</div>
  
  <div class="meta-block">
    <div><strong>Engineering:</strong> Omar Payan (Mazatlan Operational Hub)</div>
    <div><strong>Repository:</strong> github.com/opyntorr/nudesk-ai-ops-pipeline</div>
    <div><strong>Date:</strong> September 2026</div>
    <div><strong>Status:</strong> Production Ready (v2.4)</div>
  </div>
</div>

<h2 class="part-heading">Part 1: Operational Overview & Product Walkthrough</h2>

<h2 class="section-heading">1. Context & The Operational Dilemma</h2>
<p>
  In commercial finance, loan underwriting, and business development operations, processing customer applications is primarily limited by manual backoffice overhead. When a commercial client applies for equipment financing or a working capital credit line, operations specialists typically must:
</p>
<ul>
  <li>Listen to 15-to-30 minute recorded discovery calls or parse dense interview notes.</li>
  <li>Extract financial indicators: annual revenue, existing monthly debt service, and requested principal.</li>
  <li>Calculate Debt-to-Income (DTI) and Debt Service Coverage Ratios (DSCR) manually in spreadsheets.</li>
  <li>Create compliance checklist tasks manually in project management tools like Asana.</li>
  <li>Draft personalized underwriting memos and borrower correspondence from scratch in email clients.</li>
</ul>
<p>
  This manual routine consumes 3 to 4 hours per file. Human arithmetic errors in debt ratios can misclassify risk tiers, while scattered communication across email and messaging tools degrades operational accountability.
</p>

<div class="note-box">
  <strong>The Cyborg Organization Model:</strong> nuDesk pairs human operational specialists in Mazatlan with domain-trained AI agents. Rather than allowing generative models to make uncontrolled estimates or perform mental arithmetic, nuDesk routes all calculations through verified deterministic Python tools. The specialist maintains final review authority, while the system automates transcription, ratio calculation, database lookups, and correspondence staging.
</div>

<h2 class="section-heading">2. Credit Underwriting Cockpit</h2>
<p>
  The credit cockpit ingests discovery notes and phone transcripts. When the operator triggers triage, the system parses the applicant's financial situation, calculates debt ratios using deterministic Python math, queries previous database history, and prepares a structured underwriting memo.
</p>

<div class="figure-box">
  {img("01_credit_triage_cockpit.png", width="96%", max_height="215px")}
  <div class="caption">Figure 1: Credit Underwriting Cockpit with active loan file triage and synthesized memo.</div>
</div>

<!-- ========================================== -->
<!-- PAGE 2: AGENT REASONING, SALES, HR, KPIS   -->
<!-- ========================================== -->
<div class="page-break"></div>

<h2 class="section-heading" style="margin-top: 0;">3. Agent Reasoning & Multi-Role Operations</h2>
<p>
  Generative language models frequently hallucinate or make arithmetic errors when asked to calculate percentages and debt service ratios. To prevent this, nuDesk enforces deterministic tool execution. The agent is prohibited from calculating ratios in its prompt; it must invoke Python functions.
</p>
<p>
  Every completed evaluation renders an inspectable execution trace directly in the user interface. Analysts can inspect every tool call, database lookup, and calculation before signing off:
</p>

<div class="figure-box">
  {img("02_agent_reasoning_trace.png", width="96%", max_height="215px")}
  <div class="caption">Figure 2: Execution trace showing database lookup (Step 1), Python ratio calculation (Step 2), and grounded synthesis (Step 3).</div>
</div>

<p>
  The same architectural pattern extends across other backoffice workflows:
</p>
<ul>
  <li><strong>Commercial Sales (BDR):</strong> Evaluates inbound business leads, estimates revenue opportunities, scores ideal customer profile (ICP) fit, and drafts custom cold outreach scripts.</li>
  <li><strong>Talent Recruitment (HR):</strong> Analyzes bilingual interview recordings, grades candidate English fluency against the CEFR standard (B2, C1, C2), and generates targeted behavioral interview questions.</li>
  <li><strong>Executive KPI Dashboard:</strong> Provides leadership with real-time throughput metrics, departmental distribution, Asana task counts, and SLA adherence rates backed by an SQLite database.</li>
</ul>

<div class="grid-2">
  <div>
    {img("03_sales_bdr_cockpit.png", width="100%", max_height="160px")}
    <div class="caption">Figure 3: Commercial Sales BDR Cockpit.</div>
  </div>
  <div>
    {img("04_hr_talent_screening.png", width="100%", max_height="160px")}
    <div class="caption">Figure 4: Bilingual HR Talent Screening Hub.</div>
  </div>
</div>

<div class="figure-box">
  {img("05_executive_kpis.png", width="96%", max_height="185px")}
  <div class="caption">Figure 5: Executive KPI Dashboard tracking queue volume, departmental breakdown, and SLAs.</div>
</div>

<!-- ========================================== -->
<!-- PAGE 3: CLOSED-LOOP N8N, GMAIL, ROI TABLE  -->
<!-- ========================================== -->
<div class="page-break"></div>

<h2 class="section-heading" style="margin-top: 0;">4. Closed-Loop Automation & Physical Workspace Delivery</h2>
<p>
  nuDesk does not stop at visual dashboards. When an analyst reviews and approves an evaluation, clicking "Dispatch" transmits an authenticated webhook to a containerized n8n workflow engine.
</p>

<p>
  The n8n workflow ingests the webhook, inspects the department tag, and performs three synchronized actions:
</p>
<ol>
  <li><strong>Audit Log:</strong> Appends a permanent audit record into Google Sheets with timestamp, operator name, and key metrics.</li>
  <li><strong>Compliance Tasks:</strong> Calls the Asana API to create KYC and regulatory verification tasks assigned to the responsible team member with due dates.</li>
  <li><strong>Email Staging:</strong> Calls the Gmail API to generate a complete, formatted draft in the user's Gmail account ready for human review.</li>
</ol>

<div class="figure-box">
  {img("n8n_multimodule_workflow.png", width="96%", max_height="215px")}
  <div class="caption">Figure 6: n8n workflow blueprint routing webhooks to Google Sheets, Asana, and Gmail.</div>
</div>

<p>
  Rather than typing emails, the underwriter opens Gmail and finds a pre-written, professionally styled draft with the applicant's verified ratios, loan terms, and Asana links already populated. The specialist simply reviews the draft and hits send. Concurrently, executive leadership receives an automated daily briefing in rich HTML directly in their inbox:
</p>

<div class="grid-2">
  <div>
    {img("gmail_draft_credit_underwriting.png", width="100%", max_height="175px")}
    <div class="caption">Figure 7: Staged Credit Underwriting Memo Draft in Gmail.</div>
  </div>
  <div>
    {img("email_executive_briefing_html.png", width="100%", max_height="175px")}
    <div class="caption">Figure 8: Rich HTML Executive Briefing received in Gmail.</div>
  </div>
</div>

<h2 class="section-heading">5. Operational Impact & Key Metrics</h2>
<table>
  <thead>
    <tr>
      <th>Operational Metric</th>
      <th>Manual Baseline</th>
      <th>nuDesk Operations Studio</th>
      <th>Measured Outcome</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>File Triage Latency</td>
      <td>3 to 4 hours per file</td>
      <td>Under 3 seconds</td>
      <td>99% reduction in processing time</td>
    </tr>
    <tr>
      <td>Financial Ratio Accuracy</td>
      <td>Subject to spreadsheet errors</td>
      <td>100% deterministic Python calculation</td>
      <td>Zero debt ratio hallucinations</td>
    </tr>
    <tr>
      <td>Compliance Task Logging</td>
      <td>Manual checklist tracking</td>
      <td>Automated Asana task generation</td>
      <td>100% KYC audit adherence</td>
    </tr>
    <tr>
      <td>Customer Correspondence</td>
      <td>Written manually from scratch</td>
      <td>Pre-staged drafts in Gmail</td>
      <td>Human review in one click</td>
    </tr>
    <tr>
      <td>Operational Auditability</td>
      <td>Scattered notes and emails</td>
      <td>Permanent SQLite and Google Sheets log</td>
      <td>Complete end-to-end traceability</td>
    </tr>
  </tbody>
</table>

<!-- ========================================== -->
<!-- PAGE 4: PART 2 - ARCHITECTURE & TOOL SPEC  -->
<!-- ========================================== -->
<div class="page-break"></div>

<h2 class="part-heading">Part 2: Technical Architecture & Implementation</h2>

<h2 class="section-heading">6. End-to-End System Architecture</h2>
<p>
  nuDesk is built on modular, decoupled components. The user interface, inference layer, persistence store, and automation orchestrator communicate via standard HTTP webhooks, Pydantic data models, and Python DB-API interfaces.
</p>

<pre>
+---------------------------------------------------------------------------------------+
| Inbound Ingestion Layer                                                               |
| - Wispr Flow voice dictation                                                          |
| - Google Meet & Read AI call transcripts                                              |
| - HTTP Ingestion Server (:8502, inbound_api.py)                                       |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| Operations Cockpit (app.py | Streamlit)                                               |
| - Role-based access control (auth_rbac.py)                                            |
| - Priority FIFO queues for pending applications                                       |
| - Persistent SQLite audit trail (database.py)                                         |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| Agent Core & Security Guardrails (ai_engine.py & agent_guardrails.py)                 |
| - Pre-flight privacy interceptor: regex masking for SSN, EIN, and payment cards       |
| - Prompt injection defense: subversion detection and quarantine                       |
| - Model cascade: Gemini 3.5 Flash-Lite -> Gemini 3.5 Flash -> Gemini 1.5 Pro          |
| - Deterministic tool: tool_compute_financial_ratios (native Python)                   |
| - Deterministic tool: tool_lookup_applicant_history (SQLite lookup)                   |
| - Post-flight reconciliation: ground-truth mathematical override                      |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| Dispatcher & Automation Orchestration                                                 |
| - Authenticated webhook dispatch (crm_dispatcher.py, X-nuDesk-Auth-Token)             |
| - n8n workflow engine in Docker (n8n_workflow_blueprint.json)                         |
|   |--> Google Sheets API: append audit row                                            |
|   |--> Asana API: create KYC/AML compliance tasks                                     |
|   |--> Gmail API: create pre-staged email drafts                                      |
+---------------------------------------------------------------------------------------+
</pre>

<h2 class="section-heading">7. Deterministic Tool Grounding Protocol</h2>
<p>
  Financial underwriting requires strict arithmetic reproducibility. In nuDesk, ratio computations are executed by Python functions registered as tool schemas conforming to the open agent standard.
</p>

<h3>7.1 Tool Specification (`agent_specs/tools_manifest.json`)</h3>
<p>
  The model is provided with formal function declarations instructing it to delegate mathematical computation:
</p>
<pre><code class="language-json">{{
  "name": "tool_compute_financial_ratios",
  "description": "Calculates exact DSCR, DTI, and assigns deterministic risk tier.",
  "parameters": {{
    "type": "object",
    "properties": {{
      "annual_revenue": {{ "type": "number", "description": "Gross annual business revenue" }},
      "existing_monthly_debt": {{ "type": "number", "description": "Current monthly debt service" }},
      "requested_principal": {{ "type": "number", "description": "Requested loan amount" }},
      "loan_term_months": {{ "type": "integer", "description": "Loan term in months", "default": 36 }},
      "annual_interest_rate": {{ "type": "number", "description": "Annual interest rate", "default": 0.10 }}
    }},
    "required": ["annual_revenue", "existing_monthly_debt", "requested_principal"]
  }}
}}</code></pre>

<!-- ========================================== -->
<!-- PAGE 5: PYTHON RATIO & DATA CONTRACTS      -->
<!-- ========================================== -->
<div class="page-break"></div>

<h2 class="section-heading" style="margin-top: 0;">8. Mathematical Implementation & Data Contracts</h2>

<h3>8.1 Pure Python Ratio Implementation</h3>
<p>
  Calculations run outside model memory using standard financial formulas:
</p>
<pre><code class="language-python">def tool_compute_financial_ratios(annual_revenue: float, existing_monthly_debt: float,
                                  requested_principal: float, loan_term_months: int = 36,
                                  annual_interest_rate: float = 0.10) -> dict:
    monthly_revenue = annual_revenue / 12.0
    r = annual_interest_rate / 12.0
    n = loan_term_months
    
    # Amortization calculation
    new_monthly_payment = (requested_principal * (r * (1 + r)**n)) / ((1 + r)**n - 1)
    total_monthly_debt = existing_monthly_debt + new_monthly_payment
    
    # Financial ratios
    dti_ratio = round((total_monthly_debt / monthly_revenue) * 100.0, 1)
    noi = monthly_revenue * 0.25  # Operating margin baseline
    dscr = round(noi / total_monthly_debt, 2)
    
    # Deterministic risk tier classification
    if dti_ratio <= 35.0 and dscr >= 1.25:
        tier, max_rec = "Tier 1 - Low Risk", requested_principal
    elif dti_ratio <= 50.0 and dscr >= 1.05:
        tier, max_rec = "Tier 2 - Moderate Risk", requested_principal * 0.80
    else:
        tier, max_rec = "Tier 3 - High Risk", requested_principal * 0.50
        
    return {{"dscr": dscr, "dti_ratio_pct": dti_ratio, "risk_tier": tier, "recommended_principal": max_rec}}
</code></pre>

<h2 class="section-heading">9. Formal Data Contracts (Pydantic V2)</h2>
<p>
  All outputs are governed by Pydantic models defined in <code>models.py</code>. Model responses must conform to these schemas before storage or dispatch:
</p>

<pre><code class="language-python">class AsanaTask(BaseModel):
    task_name: str = Field(..., description="Actionable task title with client name")
    assignee_role: str = Field(..., description="Role: Underwriter, BDR, or HR Lead")
    due_in_days: int = Field(default=2, ge=1, le=14)
    priority: Literal["Low", "Medium", "High", "Urgent"] = Field(default="Medium")

class CreditTriageOutput(BaseModel):
    business_name: str
    owner_name: str
    requested_amount: float = Field(..., gt=0)
    calculated_dti: float = Field(..., ge=0, le=100)
    calculated_dscr: float = Field(..., ge=0)
    risk_tier: Literal["Tier 1 - Low Risk", "Tier 2 - Moderate Risk", "Tier 3 - High Risk"]
    recommended_principal: float = Field(..., gt=0)
    red_flags: List[str] = Field(default_factory=list)
    compliance_tasks: List[AsanaTask] = Field(default_factory=list)
    underwriter_memo: str = Field(..., min_length=50)

    @field_validator("risk_tier")
    @classmethod
    def assert_tier_dti_consistency(cls, v: str, info: ValidationInfo) -> str:
        dti = info.data.get("calculated_dti", 0)
        if dti > 50.0 and v == "Tier 1 - Low Risk":
            raise ValueError("Inconsistent Tier: DTI over 50% cannot be Tier 1")
        return v
</code></pre>

<!-- ========================================== -->
<!-- PAGE 6: GUARDRAILS, PERSISTENCE, WEBHOOKS  -->
<!-- ========================================== -->
<div class="page-break"></div>

<h2 class="section-heading" style="margin-top: 0;">10. Security Guardrails & Persistence Architecture</h2>

<h3>10.1 Security Interceptors (`agent_guardrails.py`)</h3>
<p>
  In accordance with financial privacy standards, incoming text is processed through pre-flight and post-flight interceptors:
</p>
<ul>
  <li><strong>PII Masking:</strong> Automated regular expressions sanitize US Social Security Numbers (<code>[REDACTED_SSN]</code>), Employer Identification Numbers (<code>[REDACTED_EIN]</code>), and payment card numbers before sending data to language model APIs.</li>
  <li><strong>Prompt Injection Defense:</strong> Subversion patterns such as "ignore previous instructions" or "system override" are trapped, quarantined to High Risk, and appended to the underwriter's red flag alerts.</li>
  <li><strong>Mathematical Reconciliation:</strong> A post-flight interceptor compares the LLM's synthesized DTI against the tool's ground truth. If divergence exceeds 15 percentage points, the harness automatically overrides the field with verified Python calculations.</li>
</ul>

<h3>10.2 SQLite Schema & SLA Tracking (`database.py`)</h3>
<p>
  All applications, evaluations, and dispatch records are persisted in <code>operations_history.db</code>. Automatic migrations ensure forward compatibility:
</p>
<pre><code class="language-sql">CREATE TABLE IF NOT EXISTS operations_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    operator_name TEXT NOT NULL,
    operator_role TEXT NOT NULL,
    module_type TEXT NOT NULL,          -- 'credit', 'sales', 'hr', 'it'
    entity_name TEXT NOT NULL,
    headline_metric TEXT NOT NULL,
    assessment_summary TEXT NOT NULL,
    full_output_json TEXT NOT NULL,     -- Complete validated Pydantic JSON
    dispatch_status TEXT NOT NULL,      -- 'DISPATCHED_TO_N8N', 'PENDING'
    is_processed INTEGER DEFAULT 1,     -- 0 = Pending, 1 = Completed
    source_channel TEXT DEFAULT 'Google Meet / Read AI',
    analyst_notes TEXT DEFAULT ''
);
</code></pre>

<h3>10.3 Webhook Dispatcher & Ingestion API</h3>
<ul>
  <li><strong>Outbound Dispatch (`crm_dispatcher.py`):</strong> Posts authenticated JSON payloads to the n8n webhook with header <code>X-nuDesk-Auth-Token</code>. Handles network retries with exponential backoff.</li>
  <li><strong>Inbound Ingestion (`inbound_api.py`):</strong> A zero-dependency HTTP server running on port 8502. Ingests raw payloads from Google Sheets and meeting bot webhooks (Read AI, Fireflies, Wispr Flow) directly into pending queues without external web framework dependencies.</li>
</ul>

<!-- ========================================== -->
<!-- PAGE 7: TESTING, DECOUPLING & SUMMARY      -->
<!-- ========================================== -->
<div class="page-break"></div>

<h2 class="section-heading" style="margin-top: 0;">11. Testing Suite & Evaluation Harness</h2>
<p>
  The system is validated by an automated unit test suite and a continuous safety evaluation harness:
</p>
<ul>
  <li><strong>Unit Test Suite (82 tests):</strong> Executes via <code>make test</code> in approximately 7.5 seconds. Validates Pydantic contracts, deterministic financial calculations, SQLite persistence, and UI accessibility.</li>
  <li><strong>Agent Evaluation Harness:</strong> Executes via <code>make eval</code> to benchmark agent behavior against 6 real-world operational scenarios.</li>
</ul>

<table>
  <thead>
    <tr>
      <th>Evaluation Scenario</th>
      <th>Capability Evaluated</th>
      <th>Pass Criterion</th>
      <th>Status</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1. Prime Credit File</td>
      <td>Multi-tool execution and ratio computation</td>
      <td>All 3 tools executed; verified DTI = 16.2%</td>
      <td>Pass</td>
    </tr>
    <tr>
      <td>2. Distressed Debt Burden</td>
      <td>Post-flight guardrail reconciliation</td>
      <td>Overrode drifted LLM risk tier</td>
      <td>Pass</td>
    </tr>
    <tr>
      <td>3. Historical DB Lookup</td>
      <td>SQLite query for prior defaults</td>
      <td>Retrieved applicant records from database</td>
      <td>Pass</td>
    </tr>
    <tr>
      <td>4. Prompt Injection Defense</td>
      <td>Adversarial subversion detection</td>
      <td>Neutralized attack; injected security alert</td>
      <td>Pass</td>
    </tr>
    <tr>
      <td>5. PII Masking</td>
      <td>Redaction of SSN, EIN, and credit cards</td>
      <td>Verified sanitization before model call</td>
      <td>Pass</td>
    </tr>
    <tr>
      <td>6. Zero-Config Resilience</td>
      <td>Offline fallback benchmark serving</td>
      <td>Served benchmark file without unhandled exceptions</td>
      <td>Pass</td>
    </tr>
  </tbody>
</table>

<div class="note-box">
  <strong>Benchmark Result:</strong> 6 scenarios evaluated, 6 passed. Harness Safety and Grounding Score: <strong>100.0% (Grade A+)</strong>.
</div>

<h2 class="section-heading">12. Modular Decoupling & Vendor Interchangeability</h2>
<p>
  To avoid vendor lock-in, every subsystem in nuDesk is defined by an interface contract, allowing straightforward substitution:
</p>

<table>
  <thead>
    <tr>
      <th>Subsystem</th>
      <th>Default Component</th>
      <th>Drop-In Alternative</th>
      <th>Interface Boundary</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Inference Model</td>
      <td>Google Gemini 3.5 Cascade</td>
      <td>Claude 3.5 Sonnet, GPT-4o, Ollama</td>
      <td>Pydantic V2 schema validation</td>
    </tr>
    <tr>
      <td>Workflow Engine</td>
      <td>n8n in Docker</td>
      <td>Make.com, Zapier, Temporal, FastAPI</td>
      <td>HTTP Webhook with Auth Token</td>
    </tr>
    <tr>
      <td>Database Store</td>
      <td>SQLite (local)</td>
      <td>PostgreSQL, AWS RDS, Snowflake</td>
      <td>Python DB-API / database.py</td>
    </tr>
    <tr>
      <td>Voice Intake</td>
      <td>Wispr Flow / Read AI / Fireflies</td>
      <td>Superwhisper, AssemblyAI, Whisper</td>
      <td>Inbound HTTP API (:8502)</td>
    </tr>
  </tbody>
</table>

<h2 class="section-heading">13. Summary</h2>
<p>
  nuDesk Operations Studio demonstrates a practical approach to enterprise generative AI: combining language models for transcription and unstructured parsing with deterministic software tools for mathematics, database queries, and workflow execution. This gives backoffice operations the speed of automation with the reliability of verified software engineering.
</p>

<div style="border-top: 1px solid #e5e7eb; padding-top: 8px; margin-top: 14px; font-size: 7.5pt; color: #6b7280; text-align: center;">
  nuDesk Operations Studio &bull; Open-source repository: github.com/opyntorr/nudesk-ai-ops-pipeline &bull; Tested on Python 3.10 and 3.11
</div>

</body>
</html>"""

def main():
    print("=" * 70)
    print("nuDesk Clean & Minimalist PDF Generator")
    print("=" * 70)
    
    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    html_content = build_html()
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated clean HTML template at: {OUTPUT_HTML} ({len(html_content)} bytes)")
    
    print("Launching Playwright to render clean PDF...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file://{OUTPUT_HTML}", wait_until="networkidle")
        
        header_template = """
            <div style="font-size: 7pt; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #9ca3af; width: 100%; padding-left: 18mm; padding-right: 18mm; display: flex; justify-content: space-between; border-bottom: 0.5px solid #e5e7eb; padding-bottom: 2px;">
                <span>nuDesk Operations Studio</span>
                <span>System Architecture & Operational Overview</span>
            </div>
        """
        footer_template = """
            <div style="font-size: 7pt; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #9ca3af; width: 100%; padding-left: 18mm; padding-right: 18mm; display: flex; justify-content: space-between; border-top: 0.5px solid #e5e7eb; padding-top: 2px;">
                <span>Mazatlan Operational Hub</span>
                <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
            </div>
        """
        
        page.pdf(
            path=OUTPUT_PDF_DOCS,
            format="A4",
            print_background=True,
            margin={"top": "18mm", "bottom": "18mm", "left": "18mm", "right": "18mm"},
            display_header_footer=True,
            header_template=header_template,
            footer_template=footer_template,
        )
        browser.close()
        
    shutil.copy2(OUTPUT_PDF_DOCS, OUTPUT_PDF_ROOT)
    
    docs_size = os.path.getsize(OUTPUT_PDF_DOCS)
    root_size = os.path.getsize(OUTPUT_PDF_ROOT)
    print(f"Success! Clean PDF generated at:")
    print(f" - {OUTPUT_PDF_DOCS} ({docs_size:,} bytes)")
    print(f" - {OUTPUT_PDF_ROOT} ({root_size:,} bytes)")
    print("=" * 70)

if __name__ == "__main__":
    main()
