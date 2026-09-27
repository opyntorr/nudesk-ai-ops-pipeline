"""
Synthetic Dataset & Supporting Document Engine for nuDesk Operations Studio.
Generates realistic, production-grade financial statements, bank statement audits,
AR aging schedules, factoring term sheets, candidate resumes, and test scorecards.
Provides both in-memory downloadable objects for Streamlit and disk-persisted files.
"""
import os
import re
import csv
import io
import json
from typing import Dict, Any, List, Optional

DATASETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "synthetic_datasets")


def slugify(text: str) -> str:
    """Convert text into a clean file-system-safe identifier."""
    clean = re.sub(r'[^a-zA-Z0-9\s_-]', '', text.split('(')[0])
    return re.sub(r'[\s-]+', '_', clean.strip()).lower()


def render_dossier_links_html(links: List[Dict[str, str]]) -> str:
    """Render a responsive horizontal badge ribbon of verified cloud links."""
    pills = []
    for l in links:
        label = l.get("label", "Document")
        url = l.get("url", "#")
        badge = l.get("badge", "badge-navy")
        pills.append(
            f'<a href="{url}" target="_blank" style="text-decoration:none; display:inline-flex; align-items:center; margin-right:0.6rem; margin-bottom:0.55rem;">'
            f'<span class="nudesk-badge {badge}" style="cursor:pointer; font-size:0.75rem; padding:0.32rem 0.7rem; border-radius:4px;">'
            f'{label} &nearr;</span></a>'
        )
    return f'<div style="margin-bottom:0.85rem; display:flex; flex-wrap:wrap; align-items:center;">{"".join(pills)}</div>'


# ============================================================================
# CREDIT OPERATIONS SYNTHETIC GENERATORS
# ============================================================================

def generate_credit_dossier(entity_name: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    slug = slugify(entity_name)
    req_amt = (payload or {}).get("requested_amount", 125000)
    collateral = (payload or {}).get("collateral", "Commercial Equipment")
    risk_tier = (payload or {}).get("risk_tier", "Low Risk")
    dti = (payload or {}).get("dti", 0.24)

    # 1. Bank Statement Audit CSV
    bank_csv_io = io.StringIO()
    writer = csv.writer(bank_csv_io)
    writer.writerow(["Date", "Transaction_ID", "Description", "Category", "Debit_USD", "Credit_USD", "Running_Balance_USD"])
    
    # 12 representative transactions showing cash flow
    base_balance = req_amt * 0.45
    txns = [
        ("2026-09-02", f"ACH-{slug[:4]}-0101", "CLIENT WIRE SETTLEMENT - FLEET ACCT #884", "Client Revenue", 0.0, req_amt * 0.22, base_balance + req_amt * 0.22),
        ("2026-09-05", f"CHK-{slug[:4]}-0102", "PAYROLL PROCESSING W/E 09/04 - DIRECT DEBIT", "Payroll", req_amt * 0.08, 0.0, base_balance + req_amt * 0.14),
        ("2026-09-08", f"ACH-{slug[:4]}-0103", "WHOLESALE PARTS & INVENTORY SUPPLIES", "COGS", req_amt * 0.05, 0.0, base_balance + req_amt * 0.09),
        ("2026-09-12", f"ACH-{slug[:4]}-0104", "COMMERCIAL CONTRACT PROGRESS BILLING", "Client Revenue", 0.0, req_amt * 0.28, base_balance + req_amt * 0.37),
        ("2026-09-15", f"ACH-{slug[:4]}-0105", "FACILITY COMMERCIAL LEASE / WAREHOUSE", "Facility Rent", req_amt * 0.04, 0.0, base_balance + req_amt * 0.33),
        ("2026-09-18", f"ACH-{slug[:4]}-0106", "UTILITY & THREE-PHASE POWER DIRECT DEBIT", "Utilities", req_amt * 0.02, 0.0, base_balance + req_amt * 0.31),
        ("2026-09-21", f"ACH-{slug[:4]}-0107", "ENTERPRISE FLEET MAINTENANCE INVOICE", "Client Revenue", 0.0, req_amt * 0.19, base_balance + req_amt * 0.50),
        ("2026-09-24", f"ACH-{slug[:4]}-0108", "EXISTING SENIOR EQUIPMENT LEASE DEBIT", "Debt Service", req_amt * 0.03, 0.0, base_balance + req_amt * 0.47),
        ("2026-09-26", f"CHK-{slug[:4]}-0109", "PAYROLL PROCESSING W/E 09/25 - DIRECT DEBIT", "Payroll", req_amt * 0.08, 0.0, base_balance + req_amt * 0.39),
    ]
    for row in txns:
        writer.writerow([row[0], row[1], row[2], row[3], f"{row[4]:.2f}", f"{row[5]:.2f}", f"{row[6]:.2f}"])
    bank_csv_content = bank_csv_io.getvalue()

    # 2. Financial Statements P&L CSV
    pnl_csv_io = io.StringIO()
    pnl_writer = csv.writer(pnl_csv_io)
    pnl_writer.writerow(["Month", "Gross_Billings_USD", "COGS_USD", "Gross_Margin_Pct", "Operating_Expenses_USD", "EBITDA_USD", "Existing_Debt_USD", "Free_Cash_Flow_USD"])
    
    monthly_rev = req_amt * 0.42
    for m_idx, m_name in enumerate(["Oct-25", "Nov-25", "Dec-25", "Jan-26", "Feb-26", "Mar-26", "Apr-26", "May-26", "Jun-26", "Jul-26", "Aug-26", "Sep-26"]):
        mult = 1.0 + (m_idx % 4) * 0.04
        rev = monthly_rev * mult
        cogs = rev * 0.46
        opex = rev * 0.28
        ebitda = rev - cogs - opex
        debt = req_amt * 0.035
        fcf = ebitda - debt
        pnl_writer.writerow([
            m_name, f"{rev:.2f}", f"{cogs:.2f}", "54.0%", f"{opex:.2f}", f"{ebitda:.2f}", f"{debt:.2f}", f"{fcf:.2f}"
        ])
    pnl_csv_content = pnl_csv_io.getvalue()

    # 3. Equipment Quote / Collateral Appraisal
    collateral_text = f"""================================================================================
NUDESK COMMERCIAL UNDERWRITING - COLLATERAL APPRAISAL & VENDOR QUOTE
================================================================================
Entity Name:           {entity_name}
Facility Requested:    ${req_amt:,.2f} USD
Appraisal Date:        2026-09-20
Assigned Underwriter:  Robert Martinez (Senior Credit Officer)
Collateral Asset:      {collateral}
Lien Priority:         First Position Commercial UCC-1 Purchase Money Security Interest
Appraised Market Val:  ${req_amt * 1.18:,.2f} USD
Orderly Liquidation:   ${req_amt * 0.88:,.2f} USD (88% advance coverage)
Vendor Invoice Ref:    VND-2026-TX-{slug[:5].upper()}-8839

PHYSICAL ASSET SPECIFICATIONS:
- Primary Manufacturer: Rotary Lift / Mazak Commercial Industrial Systems
- Condition: Factory New (Certified Tier-1 Commercial Warranty 36 Months)
- Serial Numbers: Verified SN-{slug[:3].upper()}-9948201 / SN-{slug[:3].upper()}-9948202
- Delivery & Installation Location: Verified business premises
- UCC-1 Search Status: Zero competing PMSI filings on record (County & Secretary of State)

UNDERWRITER COLLATERAL ASSESSMENT:
Asset provides strong primary repayment defense. Orderly liquidation exceeds requested principal
by comfortable 12% safety margin. Direct vendor disbursement required upon closing.
================================================================================"""

    # 4. Executive Credit Memorandum
    memo_text = f"""# Executive Underwriting Memorandum
**Borrower:** {entity_name}  
**Loan Facility:** ${req_amt:,.2f} USD Term Loan | 36 Months  
**Underwriter:** Robert Martinez, Senior Credit Officer  
**Risk Classification:** {risk_tier} | Calculated DTI: {dti:.2f} | DSCR: 1.41x  

---

### 1. Business Profile & Historical Performance
{entity_name} demonstrates resilient historical cash generation across commercial and fleet accounts.
The 12-month bank audit verifies consistent deposit velocity with zero uncollected funds fees and no Merchant Cash Advance (MCA) stacking.

### 2. Purpose of Financing
Capital will fund immediate acquisition of {collateral}. Increased operational capacity directly drives revenue expansion by removing current turnaround bottlenecks.

### 3. Credit Structure & Covenants
- **Principal:** ${req_amt:,.2f} USD
- **Interest Rate:** WSJ Prime + 3.25% Floating
- **Amortization:** 36 Monthly Principal & Interest installments
- **Collateral:** First lien on equipment via filed UCC-1 financing statement
- **Guarantors:** Personal guaranty of managing principals

### 4. Recommendation & Sign-Off
Approved unanimously by nuDesk Credit Committee. Advance to document execution and loan boarding.
"""

    return {
        "links": [
            {"label": "Google Drive Financial Vault", "url": f"https://drive.google.com/drive/folders/nudesk-credit-{slug}", "badge": "badge-teal"},
            {"label": "nuDesk LOS Deal Room", "url": f"https://app.nudesk.ai/los/loans/{slug}", "badge": "badge-green"},
            {"label": "Read AI Discovery Recording", "url": f"https://app.read.ai/analytics/meetings/rec-{slug}", "badge": "badge-navy"},
            {"label": "Texas SOS UCC-1 Registry", "url": f"https://direct.sos.state.tx.us/ucc/search?entity={slug}", "badge": "badge-navy"},
        ],
        "files": [
            {
                "name": "12-Month Bank Statement Audit (CSV)",
                "file_name": f"{slug}_bank_statements_audit.csv",
                "content": bank_csv_content,
                "mime": "text/csv",
                "description": "Full transactional breakdown of client deposits, operating disbursements, and daily balances."
            },
            {
                "name": "Financial P&L Statements (CSV)",
                "file_name": f"{slug}_pnl_cash_flow.csv",
                "content": pnl_csv_content,
                "mime": "text/csv",
                "description": "12-month EBITDA, gross margin, and debt service coverage reconciliation."
            },
            {
                "name": "Collateral Appraisal & Quote (TXT)",
                "file_name": f"{slug}_collateral_appraisal.txt",
                "content": collateral_text,
                "mime": "text/plain",
                "description": "Certified equipment valuation, vendor quote reference, and UCC-1 lien search report."
            },
            {
                "name": "Executive Credit Memo (MD)",
                "file_name": f"{slug}_credit_memorandum.md",
                "content": memo_text,
                "mime": "text/markdown",
                "description": "Full signed underwriting memorandum with risk covenants and committee sign-off."
            }
        ],
        "transcript": f"""[00:00:03] Underwriter (nuDesk Credit Ops): Good morning. Thank you for connecting on our recorded intake line regarding {entity_name}.
[00:00:12] Principal / Applicant: Thanks for having us on. We are moving forward on our equipment expansion and want to finalize the capital facility.
[00:00:24] Underwriter: Excellent. We reviewed your 12-month deposit records and preliminary vendor invoice for ${req_amt:,.2f} USD. What is the expected delivery timeline on the equipment?
[00:00:36] Principal: The manufacturer has the units staged in Houston. As soon as the wire clears, delivery and calibration take less than 5 business days.
[00:00:48] Underwriter: Perfect. Your debt-service ratio is calculated at 1.41x, which comfortably qualifies under our standard lending box.
[00:01:02] Principal: Great news. We'll sign the closing documents via DocuSign today.
[00:01:14] Underwriter: Documents are staged in your Google Workspace vault. We look forward to funding your expansion."""
    }


# ============================================================================
# COMMERCIAL SALES SYNTHETIC GENERATORS
# ============================================================================

def generate_sales_dossier(entity_name: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    slug = slugify(entity_name)
    arr = (payload or {}).get("arr", 2100000)
    fleet = (payload or {}).get("fleet_size", 14)
    score = (payload or {}).get("lead_score", 88)

    # 1. Accounts Receivable Aging Schedule (CSV)
    ar_csv_io = io.StringIO()
    ar_writer = csv.writer(ar_csv_io)
    ar_writer.writerow(["Invoice_No", "Debtor_Shipper_Broker", "Invoice_Date", "Due_Date", "Amount_USD", "Days_Outstanding", "Aging_Bracket", "Credit_Insurance_Status"])
    
    brokers = [
        ("C.H. Robinson Worldwide", 48, arr * 0.045, "Approved (Grade A)"),
        ("Total Quality Logistics (TQL)", 55, arr * 0.038, "Approved (Grade A)"),
        ("Echo Global Logistics", 38, arr * 0.029, "Approved (Grade A)"),
        ("Landstar Ranger Division", 62, arr * 0.032, "Approved (Grade A)"),
        ("Schneider Freight Systems", 44, arr * 0.025, "Approved (Grade A)"),
        ("J.B. Hunt Transport Solutions", 52, arr * 0.031, "Approved (Grade A)"),
        ("Coyote Logistics / UPS", 35, arr * 0.022, "Approved (Grade A)"),
    ]
    for idx, (broker, days, amt, ins) in enumerate(brokers, 101):
        bracket = "0-30 Days" if days <= 30 else ("31-60 Days" if days <= 60 else "61-90 Days")
        ar_writer.writerow([
            f"INV-2026-{idx}", broker, "2026-08-10", "2026-09-10", f"{amt:.2f}", days, bracket, ins
        ])
    ar_csv_content = ar_csv_io.getvalue()

    # 2. Factoring Facility Term Sheet
    facility_limit = min(max(arr * 0.15, 150000), 500000)
    term_sheet_text = f"""================================================================================
NUDESK CAPITAL - NON-RECOURSE INVOICE FACTORING TERM SHEET
================================================================================
Prospect Account:      {entity_name}
Fleet Size:            {fleet} Class-8 Tractors / Units
Annual Gross Revenue:  ${arr:,.2f} USD
Lead Urgency Score:    {score} / 100
Assigned Specialist:   Sarah Jenkins (Commercial BDR & Capital Director)

FINANCING FACILITY STRUCTURE:
- Facility Type:       Non-Recourse Commercial Invoice Factoring Line
- Maximum Credit Line: ${facility_limit:,.2f} USD Revolving Capacity
- Initial Advance:     93.0% of Verified Freight Bill Face Value
- Factoring Fee:       2.15% flat for 30 days (0.05% per diem thereafter)
- Reserve Account:     7.0% held until debtor broker remittance
- Liquidity Cadence:   Same-day Fedwire or ACH on processed freight bills
- Credit Protection:   100% insolvency risk assumption on pre-approved debtors

ACCOUNT BENEFIT SUMMARY:
Unlocks immediate same-day liquidity on 60-day freight broker receivables. Eliminates weekly
payroll strain for drivers, covers fuel card obligations, and enables fleet growth without debt.
================================================================================"""

    # 3. Sales Discovery & Outreach Dossier
    sales_dossier_text = f"""# BDR Discovery Dossier: {entity_name}
**Assigned Specialist:** Sarah Jenkins (Commercial BDR)  
**Lead Score:** {score} / 100 | High Urgency Working Capital Lead  
**Corporate Revenue:** ${arr:,.2f} ARR | Active Fleet: {fleet} Trucks  

---

### Discovery Call Notes & Pain Points
The managing partner confirms that extended broker payment cycles (averaging 54 days) are
severely choking working capital. Fuel and driver payroll are due weekly, while capital is locked in transit.

### Outreach Sequence & Staged Artifacts
- **Subject:** Accelerating {entity_name.split()[0]}'s 60-day freight receivables before payroll
- **Staged Channel:** Gmail Corporate Send via Mazatlán Operations Hub
- **Phone Pitch Objective:** Secure 10-minute underwriting rate review with Director of Logistics.
"""

    return {
        "links": [
            {"label": "HubSpot Enterprise Opportunity", "url": f"https://crm.nudesk.ai/deals/{slug}", "badge": "badge-teal"},
            {"label": "Google Sheets Live AR Aging", "url": f"https://docs.google.com/spreadsheets/d/ar-aging-{slug}", "badge": "badge-green"},
            {"label": "Fireflies.ai Call Recording", "url": f"https://app.fireflies.ai/view/sales-{slug}", "badge": "badge-navy"},
            {"label": "FMCSA Carrier Safety Profile", "url": f"https://safer.fmcsa.dot.gov/query.asp?searchtype=ANY&string={slug}", "badge": "badge-navy"},
        ],
        "files": [
            {
                "name": "Accounts Receivable Aging Schedule (CSV)",
                "file_name": f"{slug}_ar_aging_schedule.csv",
                "content": ar_csv_content,
                "mime": "text/csv",
                "description": "Detailed invoice aging schedule across Tier-1 freight brokers with credit insurance verification."
            },
            {
                "name": "Factoring Facility Term Sheet (TXT)",
                "file_name": f"{slug}_factoring_term_sheet.txt",
                "content": term_sheet_text,
                "mime": "text/plain",
                "description": "Pre-approved non-recourse invoice factoring structure with advance rates and fee schedules."
            },
            {
                "name": "BDR Sales Discovery Dossier (MD)",
                "file_name": f"{slug}_sales_discovery_dossier.md",
                "content": sales_dossier_text,
                "mime": "text/markdown",
                "description": "Comprehensive lead evaluation, BDR objection notes, and customized outreach copy."
            }
        ],
        "transcript": f"""[00:00:01] BDR (Sarah Jenkins): Hello, this is Sarah with nuDesk Capital. Am I speaking with operations at {entity_name}?
[00:00:08] Managing Partner: Yes, this is managing operations. What is this regarding?
[00:00:15] BDR: I'm reaching out because we work with regional carriers running {fleet} units in your corridor. Most operators we speak with are dealing with brokers taking 50 to 60 days to pay, which creates huge cash flow drag on weekly driver payroll.
[00:00:30] Managing Partner: You hit the nail on the head. C.H. Robinson and Landstar are taking nearly two months right now. We're having to hold back on hiring more drivers.
[00:00:41] BDR: That's exactly why we set up our same-day non-recourse factoring program. We advance 93% on clean freight bills within 4 hours, and assume 100% of the broker credit risk.
[00:00:54] Managing Partner: 93% advance sounds very competitive. What are your fees?
[00:01:02] BDR: Flat 2.15% for the first 30 days with zero lock-in contracts. I have our complete term sheet and AR aging model ready to send over.
[00:01:15] Managing Partner: Send it over to my direct inbox. Let's schedule a 10-minute walkthrough tomorrow morning."""
    }


# ============================================================================
# HR TALENT OPERATIONS SYNTHETIC GENERATORS
# ============================================================================

def generate_hr_dossier(entity_name: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    slug = slugify(entity_name)
    fit_score = (payload or {}).get("candidate_fit_score", 91)
    psico_score = (payload or {}).get("psychometrics_score", 92)
    test_score = (payload or {}).get("knowledge_test_score", 94)
    role = (payload or {}).get("applied_role", "Senior Bilingual Credit Analyst")
    area = (payload or {}).get("application_area", "Credit Underwriting & Risk")
    cefr = (payload or {}).get("cefr", "C1 Advanced")

    # 1. Technical Knowledge Scorecard (CSV)
    tech_csv_io = io.StringIO()
    tech_writer = csv.writer(tech_csv_io)
    tech_writer.writerow(["Evaluation_Module", "Max_Score", "Candidate_Score", "Benchmark_Cutoff", "Percentile_Rank", "Result", "Examiner_Comments"])
    
    modules = [
        ("SME Balance Sheet & P&L Reconstruction", 25, round(test_score * 0.245), 20, "96th Percentile", "Passed", "Flawless normalization of owner add-backs and tax depreciation."),
        ("Debt Service Coverage (DSCR) & Cash Flow Modeling", 25, round(test_score * 0.25), 21, "98th Percentile", "Passed", "Accurate modeling of seasonal construction revenue dip."),
        ("Bank Statement Fraud & MCA Stacking Detection", 25, round(test_score * 0.24), 20, "94th Percentile", "Passed", "Caught undisclosed second-position daily ACH debit instantly."),
        ("Bilingual Professional Underwriting Communication", 25, round(test_score * 0.255), 20, "99th Percentile", "Passed", f"Native-level professional English fluency ({cefr}). Concise memo structuring."),
    ]
    for row in modules:
        tech_writer.writerow(row)
    tech_csv_content = tech_csv_io.getvalue()

    # 2. Psychometric Evaluation Report (CSV)
    psico_csv_io = io.StringIO()
    psico_writer = csv.writer(psico_csv_io)
    psico_writer.writerow(["Competency_Dimension", "Candidate_Stanine", "Percentile", "Benchmark_Target", "Assessment_Profile", "Hiring_Risk_Level"])
    
    traits = [
        ("Analytical & Deductive Rigor", round(psico_score / 10.5), "95th Percentile", "Stanine 7+", "Exceptional data integrity and balance sheet pattern recognition", "Negligible"),
        ("Objection & Stress Resilience", round(psico_score / 11.2), "91st Percentile", "Stanine 6+", "High composure under urgent loan closing deadlines", "Negligible"),
        ("Detail Orientation & Precision", round(psico_score / 10.8), "94th Percentile", "Stanine 7+", "Meticulous verification of public records and UCC filings", "Negligible"),
        ("Speed to Execution & Autonomy", round(psico_score / 11.5), "89th Percentile", "Stanine 6+", "High self-starter drive requiring minimal supervision", "Low"),
    ]
    for row in traits:
        psico_writer.writerow(row)
    psico_csv_content = psico_csv_io.getvalue()

    # 3. Candidate Comprehensive Resume / CV (Markdown)
    resume_text = f"""# {entity_name}
**Target Role:** {role}  
**Specialization Area:** {area}  
**Location:** Mazatlán / Culiacán, Sinaloa, Mexico (Hybrid / Onsite Hub)  
**Languages:** English ({cefr} Certified), Spanish (Native)  
**Overall nuDesk Candidate Fit Score:** {fit_score} / 100 | Knowledge Test: {test_score}/100 | Psychometrics: {psico_score}/100  

---

### Professional Summary
Proven cross-border financial services professional with demonstrated track record in commercial underwriting,
credit memorandum structuring, and risk analysis for US SME borrowers. Expert in analyzing complex business tax returns,
reconstructing multi-entity cash flows, and identifying predatory MCA stacking. Fluent in English for direct communication
with US brokers, lenders, and executive management.

### Core Competencies
- US SME Credit Underwriting & Commercial Loan Structuring
- Cash Flow Reconciliation & Debt Service Coverage Ratio (DSCR) Calculation
- Fraud Detection, Bank Statement Analysis & Merchant Cash Advance (MCA) Stacking Audits
- Tools: Google Workspace (Advanced Sheets Modeling), Asana Ops Pipelines, Salesforce CRM, HubSpot
- Bilingual Communication & Stakeholder Presentation ({cefr} CEFR Validated)

### Professional Work Experience

**Senior Underwriting Specialist / Commercial BDR** | Regional Financial Services Group  
*Mazatlán, Sinaloa | 2022 - Present*
- Spearheaded initial credit review for over 350 US commercial debt applications ($50k to $1.5M USD facilities).
- Developed standardized Asana intake checklist that compressed triage decision turnaround from 48 hours to under 3 hours.
- Caught 18 instances of undisclosed secondary debt stacking, preventing over $620k USD in bad-debt defaults.
- Maintained a 98% on-time SLA adherence across peak seasonal intake cycles.

**Credit & Risk Operations Analyst** | Cross-Border Commercial Capital  
*Sinaloa, Mexico | 2020 - 2022*
- Analyzed 3 years of corporate tax returns (1120-S, 1065) and audited bank statements for fleet logistics clients.
- Authored executive credit memos directly consumed by US bank syndication partners.
- Conducted English discovery interviews with corporate principals to resolve lien and UCC-1 discrepancies.

### Education & Certifications
- **Licenciatura en Finanzas y Negocios Internacionales** | Universidad Autónoma de Sinaloa
- **Cambridge English C1/C2 Advanced Professional Business Credential**
- **Commercial Lending & Financial Statement Analysis Certification** (Moody's / RMA Aligned)
"""

    return {
        "links": [
            {"label": "Greenhouse Candidate Profile", "url": f"https://app.greenhouse.io/candidates/{slug}", "badge": "badge-teal"},
            {"label": "Google Drive Talent Dossier", "url": f"https://drive.google.com/drive/folders/hr-candidate-{slug}", "badge": "badge-green"},
            {"label": "Read AI Screening Recording", "url": f"https://app.read.ai/interviews/{slug}", "badge": "badge-navy"},
            {"label": "Cambridge English Verification", "url": f"https://verify.cambridgeenglish.org/cert/{slug}", "badge": "badge-navy"},
        ],
        "files": [
            {
                "name": "Candidate Comprehensive Resume (MD)",
                "file_name": f"{slug}_curriculum_vitae.md",
                "content": resume_text,
                "mime": "text/markdown",
                "description": "Complete verified candidate CV with career progression, metrics, and bilingual certification."
            },
            {
                "name": "Technical Knowledge Scorecard (CSV)",
                "file_name": f"{slug}_technical_scorecard.csv",
                "content": tech_csv_content,
                "mime": "text/csv",
                "description": "Module-by-module breakdown of underwriting, DSCR modeling, and fraud detection tests."
            },
            {
                "name": "Psychometric Benchmark Report (CSV)",
                "file_name": f"{slug}_psychometrics_benchmark.csv",
                "content": psico_csv_content,
                "mime": "text/csv",
                "description": "Validated evaluation across analytical rigor, resilience, and speed to execution."
            }
        ],
        "transcript": f"""[00:00:02] Recruiter (Elena Ramos): Welcome to your nuDesk talent screening, {entity_name.split()[0]}. How are you today?
[00:00:09] Candidate: Great, thank you Elena. Very excited to discuss the {role} opportunity.
[00:00:18] Recruiter: Let's start with your technical background. In US commercial debt, we often encounter applicants with seasonal revenue drops who took out merchant cash advances. Walk me through how you evaluate that.
[00:00:32] Candidate: Absolutely. When I analyze bank statements, the first thing I do is calculate the Net Operating Cash Flow minus daily debits. If I see ACH entries with daily or weekly debits from known MCA funders, I immediately calculate the effective APR and factor rate. If their DSCR drops below 1.15x after servicing that daily debt, I flag it as a high-risk stacking event and require an official payoff statement.
[00:00:58] Recruiter: Excellent answer. That matches our exact underwriting playbook. How do you feel about working directly with our US leadership in Dallas and Phoenix?
[00:01:10] Candidate: Completely comfortable. I have conducted discovery interviews and daily standups in English for over 3 years, and my Cambridge score is verified at {cefr}.
[00:01:24] Recruiter: Your scores on both the technical test ({test_score}/100) and psychometrics ({psico_score}/100) placed you in our top tier. I am advancing you directly to the hiring manager interview."""
    }


# ============================================================================
# MASTER DISPATCHER
# ============================================================================

def get_synthetic_dossier(entity_name: str, module_type: str, raw_json_str: Optional[Any] = None) -> Dict[str, Any]:
    """Retrieve or generate full synthetic dataset and document package for any entity."""
    payload = {}
    if raw_json_str:
        try:
            payload = json.loads(raw_json_str) if isinstance(raw_json_str, str) else raw_json_str
        except Exception:
            payload = {}

    mod = (module_type or "credit").lower()
    if mod == "credit":
        return generate_credit_dossier(entity_name, payload)
    elif mod == "sales":
        return generate_sales_dossier(entity_name, payload)
    else:
        return generate_hr_dossier(entity_name, payload)


def persist_all_synthetic_datasets() -> int:
    """Write synthetic datasets to the disk in data/synthetic_datasets/ for offline access."""
    sample_entities = [
        ("credit", "Lone Star Cold Storage (Houston, TX)", {"requested_amount": 150000, "collateral": "Warehouse Refrigeration", "risk_tier": "Low Risk", "dti": 0.22}),
        ("credit", "Pacific Shore Drywall (San Diego, CA)", {"requested_amount": 110000, "collateral": "GC Pay Applications", "risk_tier": "Low Risk", "dti": 0.25}),
        ("credit", "Highland Precision Machining (Fort Worth, TX)", {"requested_amount": 95000, "collateral": "Mazak 5-Axis CNC", "risk_tier": "Moderate Risk", "dti": 0.32}),
        ("credit", "Apex Fleet Repair (Dallas, TX)", {"requested_amount": 85000, "collateral": "Rotary Hydraulic Lifts", "risk_tier": "Moderate Risk", "dti": 0.28}),
        ("sales", "Desert Express Freight (El Paso, TX)", {"arr": 1800000, "fleet_size": 12, "lead_score": 88}),
        ("sales", "Sonora Freightlines (Nogales, AZ)", {"arr": 3100000, "fleet_size": 22, "lead_score": 92}),
        ("sales", "Cactus State Express (Tucson, AZ)", {"arr": 1200000, "fleet_size": 7, "lead_score": 78}),
        ("sales", "Sunbelt Logistics LLC (Phoenix, AZ)", {"arr": 2400000, "fleet_size": 14, "lead_score": 92}),
        ("hr", "Mateo Guerrero (Mazatlán, Sin.)", {"applied_role": "Commercial BDR", "application_area": "Commercial Sales & BDR", "candidate_fit_score": 88, "psychometrics_score": 85, "knowledge_test_score": 87, "cefr": "B2"}),
        ("hr", "Mariana Ochoa (Culiacán, Sin.)", {"applied_role": "Senior Underwriting Lead", "application_area": "Credit Underwriting & Risk", "candidate_fit_score": 91, "psychometrics_score": 94, "knowledge_test_score": 93, "cefr": "C2"}),
        ("hr", "Diego Carvajal (Mazatlán, Sin.)", {"applied_role": "Junior Credit Analyst", "application_area": "Credit Underwriting & Risk", "candidate_fit_score": 86, "psychometrics_score": 84, "knowledge_test_score": 82, "cefr": "B2"}),
        ("hr", "Sofia Valdez (Mazatlán, Sin.)", {"applied_role": "Senior Bilingual Credit Analyst", "application_area": "Credit Underwriting & Risk", "candidate_fit_score": 94, "psychometrics_score": 92, "knowledge_test_score": 96, "cefr": "C1"}),
    ]

    total_written = 0
    for mod, name, payload in sample_entities:
        dossier = get_synthetic_dossier(name, mod, payload)
        folder = os.path.join(DATASETS_DIR, mod, slugify(name))
        os.makedirs(folder, exist_ok=True)
        
        # Write files
        for f_item in dossier["files"]:
            file_path = os.path.join(folder, f_item["file_name"])
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f_item["content"])
            total_written += 1
            
        # Write metadata & transcript
        with open(os.path.join(folder, "dossier_meta.json"), "w", encoding="utf-8") as f:
            json.dump({
                "entity_name": name,
                "module_type": mod,
                "links": dossier["links"],
                "file_count": len(dossier["files"])
            }, f, indent=2)
            
        with open(os.path.join(folder, "archived_transcript.txt"), "w", encoding="utf-8") as f:
            f.write(dossier["transcript"])
            
    return total_written


if __name__ == "__main__":
    count = persist_all_synthetic_datasets()
    print(f"Persisted {count} synthetic files to {DATASETS_DIR}")
