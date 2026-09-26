"""
Automated Meeting Ingestion Queue (Google Meet / Read AI / Fireflies Simulator)
Simulates incoming webhook records streamed directly from meeting recorders,
eliminating manual copy-paste for operators while retaining manual fallback.
"""
from typing import Dict, Any, List
from mock_data import BENCHMARK_TRANSCRIPT, BENCHMARK_SALES_LEAD


BENCHMARK_HR_TRANSCRIPT = """
Interviewer (Elena Ramos - Talent Acquisition Specialist, nuDesk MX):
Hi Sofia, thank you for joining our video call today from Mazatlán. We're very excited to discuss the Senior Bilingual Credit Analyst position supporting our US commercial lending partner in Dallas. To start off, could you walk me through your background in underwriting and financial document review?

Candidate (Sofia Valdez):
Hello Elena, it's a pleasure. Yes, absolutely. For the past four years, I've worked as a credit analyst at a regional cross-border factoring firm here in Sinaloa. My primary responsibility has been evaluating US small-to-medium enterprise debt applications—specifically analyzing 6 months of bank statements, tax returns, P&L statements, and UCC filings. In my current workflow, I handle between 6 to 8 full file reviews daily, extracting debt service coverage ratios (DSCR), calculating unencumbered cash flows, and drafting formal Credit Memos for the credit committee.

Interviewer:
That is very relevant to our US portfolio. Since our analysts communicate directly with US underwriters, brokers, and occasionally the business owners themselves, how comfortable are you conducting live discovery calls entirely in English?

Candidate:
All of my current documentation and about 70% of my client correspondence is in English. I lived in San Diego for two years during college and have a C1 advanced certification. I feel completely comfortable discussing loan covenants, tax lien subordinations, and financial anomalies on live calls with US borrowers.

Interviewer:
Excellent. In our environment, speed and attention to detail are critical. Could you describe a time when you caught a discrepancy or red flag during an underwriting review that wasn't immediately obvious?

Candidate:
Definitely. Last quarter, an applicant submitted bank statements showing strong daily balances of over $40,000. However, while analyzing the deposits breakdown, I noticed frequent round-number credits from two other merchant cash advance (MCA) providers that weren't disclosed on their liabilities schedule. They were effectively "stacking" debt to hide a cash deficit. I flagged the unrecorded daily withdrawals, re-calculated their actual debt-to-income, and saved our firm from an imminent default. The credit officer commended the thoroughness of the memo.

Interviewer:
That is exactly the type of eagle-eye analysis we value at nuDesk. What tools do you use for workflow tracking and CRM?

Candidate:
I am very proficient in Google Workspace (especially Google Sheets for financial modeling), Asana for task and pipeline staging, and HubSpot for tracking applicant communications.

Interviewer:
Fantastic, Sofia. Your technical grasp and bilingual proficiency align strongly with what our lending team needs. I am advancing your profile to the next round with our Operations Director for a live case-study interview. Thank you for your time today!
""".strip()


INCOMING_MEETINGS_QUEUE: List[Dict[str, Any]] = [
    {
        "id": "meet_credit_01",
        "title": "Apex Fleet Repair — $85k Equipment Term Loan Discovery",
        "source": "Google Meet via Read AI",
        "received_ago": "8 mins ago",
        "type": "credit",
        "entity": "Apex Fleet Repair (Dallas, TX)",
        "contact": "Robert Martinez (Owner)",
        "transcript": BENCHMARK_TRANSCRIPT,
        "default_doc_url": "https://example.com/quotes/rotary-lift-spec-85k.pdf",
        "doc_note": "Attached quote: 2x Rotary Lift Heavy-Duty Hydraulic 12k Units ($85,400 USD)"
    },
    {
        "id": "meet_sales_02",
        "title": "Sunbelt Logistics LLC — Freight Factoring & Cash Flow Review",
        "source": "Google Meet via Fireflies.ai",
        "received_ago": "22 mins ago",
        "type": "sales",
        "entity": "Sunbelt Logistics LLC (Phoenix, AZ)",
        "contact": "Marcus Vance (Managing Director)",
        "lead_data": BENCHMARK_SALES_LEAD,
        "default_doc_url": "https://example.com/freight/sunbelt-broker-aging.pdf",
        "doc_note": "Attached AR Aging Report: 60-day outstanding broker freight bills ($140,000 USD)"
    },
    {
        "id": "meet_hr_03",
        "title": "Sofia Valdez — Senior Bilingual Credit Analyst Screening",
        "source": "Google Meet via Read AI",
        "received_ago": "35 mins ago",
        "type": "hr",
        "entity": "Sofia Valdez (Candidate)",
        "contact": "Elena Ramos (Interviewer)",
        "transcript": BENCHMARK_HR_TRANSCRIPT,
        "default_doc_url": "https://example.com/resumes/sofia-valdez-underwriter.pdf",
        "doc_note": "Attached Resume & C1 Language Certificate (Cambridge CEFR)"
    }
]


def get_queue_items_for_role(role_key: str) -> List[Dict[str, Any]]:
    if role_key == "underwriter":
        return [m for m in INCOMING_MEETINGS_QUEUE if m["type"] == "credit"]
    elif role_key == "bdr":
        return [m for m in INCOMING_MEETINGS_QUEUE if m["type"] == "sales"]
    elif role_key == "hr_recruiter":
        return [m for m in INCOMING_MEETINGS_QUEUE if m["type"] == "hr"]
    return INCOMING_MEETINGS_QUEUE
