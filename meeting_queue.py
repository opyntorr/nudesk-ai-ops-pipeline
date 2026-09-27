"""
Automated Meeting Ingestion Queue (Google Meet / Read AI / Fireflies Simulator)
nuDesk MX — Mazatlán Operations Hub & US Commercial Lending
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

GULF_COAST_TRANSCRIPT = """
Underwriter (Robert Martinez - Senior Underwriter, nuDesk MX):
Good morning, this is Robert with commercial lending underwriting. I have Captain Miller from Gulf Coast Marine Welding on the line from Galveston, Texas. Good morning, Captain Miller.

Applicant (Donald Miller - Managing Partner):
Morning Robert. Thanks for hopping on so quickly. We're looking at a $140,000 working capital line to float weekly specialized welding labor while waiting on 45-day commercial shipyard invoice reconciliations.

Underwriter:
Understood. Walk me through your top accounts and current lien status.

Applicant:
We service offshore support vessels and tugboats at Port of Galveston. Monthly billings average $62,000 with very consistent margins. We have zero open UCC-1 filings or tax liens. Our balance sheet has three fully depreciated mobile diesel welding rigs valued at $90,000. We just need faster liquidity between shipyard progress approvals.

Underwriter:
Thank you. That aligns well with our receivable-backed facility requirements. I will run our automated collateral triage now.
""".strip()

RIO_GRANDE_TRANSCRIPT = """
Underwriter (Robert Martinez):
Calling Hector Longoria, COO of Rio Grande Distribution in Laredo, Texas regarding their $210,000 factoring application.

Applicant (Hector Longoria):
Hello Robert. We run an 18-tractor cross-border dry van carrier hauling automotive components between Monterrey and Dallas. Our monthly freight billings run $92,000. Big 3 tier-one shippers pay on 60-day terms, which strains our weekly diesel fuel and driver settlements.

Underwriter:
Do you have any existing factoring covenants or bank debt?

Applicant:
We have a local credit union equipment note for $45,000 with clean payment history. No MCA debt, no liens. We want spot factoring for our top 4 creditworthy broker accounts.
""".strip()

BAJA_SALES_LEAD = """
Company: Baja Cross-Border Cold Chain
Headquarters: Otay Mesa, CA & Tijuana, B.C.
Contact: Diana Navarro (VP of Operations)
Direct: (619) 555-8921 | d.navarro@bajacoldchain.com
Fleet Size: 8 Refrigerated Multi-Temp 53ft Trailers
Reported Annual Gross Revenue: $1,600,000 USD
Primary Freight: High-value fresh avocados, berries, and seafood
Operational Bottleneck: 45-day broker payment terms causing cash strain during peak harvest seasons
Factoring Fit: Immediate non-recourse line requested with 24-hr advance against verified Bills of Lading
Preferred Term: Flexible month-to-month, no long-term volume lock-in
""".strip()

ALAMO_SALES_LEAD = """
Company: Alamo Industrial Coatings
Headquarters: San Antonio, TX
Contact: Jorge Villarreal (Owner & General Manager)
Direct: (210) 555-4309 | jorge@alamocoatings.com
Annual Revenue: $980,000 USD
Core Business: Commercial sandblasting, water tower restoration, and epoxy containment coatings
Current Pipeline: 2 active municipal contracts with San Antonio Water System ($320k unbilled)
Operational Bottleneck: Weekly payroll for 16 certified blasters requires progress billing liquidity
Target Facility: $100k revolving credit or progress invoice purchase
""".strip()

CARLOS_MENDOZA_TRANSCRIPT = """
Interviewer (Elena Ramos - nuDesk MX):
Hello Carlos, welcome. We are interviewing for the Commercial BDR position driving outbound commercial lending and factoring accounts across Texas and Arizona.

Candidate (Carlos Mendoza):
Hi Elena. Thank you. For the last 3 years, I've worked as an outbound sales development representative for a 3PL freight broker in Guadalajara, dialing 60-80 cold calls daily to US trucking and manufacturing executives. I consistently achieved 115% of my qualified demo quota.

Interviewer:
How do you handle rapid commercial English conversations when speaking to busy dispatchers and business owners?

Candidate:
I lived in Tucson for a year during high school and hold a B2+ business certification. I know freight terminology like deadhead, detention, and quick-pay inside and out. I love cold calling and building trust in the first 15 seconds.
""".strip()

VALERIA_BELTRAN_TRANSCRIPT = """
Interviewer (Elena Ramos - nuDesk MX):
Hello Valeria. Tell me about your background sourcing bilingual financial talent in Northwest Mexico.

Candidate (Valeria Beltrán):
Hi Elena. Over the last 5 years in Culiacán and Mazatlán, I have led talent acquisition for multinational shared services centers. I've placed over 120 bilingual financial analysts, credit underwriters, and customer operations specialists. I specialize in CEFR C1/C2 language evaluations and technical case study facilitation.
""".strip()


INCOMING_MEETINGS_QUEUE: List[Dict[str, Any]] = [
    # Credit Queue
    {
        "id": "meet_credit_01",
        "title": "Apex Fleet Repair — $85k Equipment Term Loan Discovery",
        "source": "Google Meet via Read AI",
        "received_ago": "8 mins ago",
        "type": "credit",
        "entity": "Apex Fleet Repair (Dallas, TX)",
        "contact": "Robert Martinez (Owner)",
        "headline": "$85,000 USD | Equipment Term Loan",
        "transcript": BENCHMARK_TRANSCRIPT,
        "default_doc_url": "https://example.com/quotes/rotary-lift-spec-85k.pdf",
        "doc_note": "Attached quote: 2x Rotary Lift Heavy-Duty Hydraulic 12k Units ($85,400 USD)"
    },
    {
        "id": "meet_credit_02",
        "title": "Gulf Coast Marine Welding — $140k Working Capital Facility",
        "source": "Google Meet via Fireflies.ai",
        "received_ago": "42 mins ago",
        "type": "credit",
        "entity": "Gulf Coast Marine Welding (Galveston, TX)",
        "contact": "Donald Miller (Managing Partner)",
        "headline": "$140,000 USD | Working Capital Line",
        "transcript": GULF_COAST_TRANSCRIPT,
        "default_doc_url": "https://example.com/contracts/galveston-shipyard-master-services.pdf",
        "doc_note": "Attached: Port of Galveston drydock master subcontract ($140,000 USD)"
    },
    {
        "id": "meet_credit_03",
        "title": "Rio Grande Distribution — $210k Cross-Border Factoring Line",
        "source": "Google Meet via Read AI",
        "received_ago": "3 hours ago",
        "type": "credit",
        "entity": "Rio Grande Distribution (Laredo, TX)",
        "contact": "Hector Longoria (COO)",
        "headline": "$210,000 USD | Cross-Border Factoring",
        "transcript": RIO_GRANDE_TRANSCRIPT,
        "default_doc_url": "https://example.com/freight/laredo-bol-reconciliation.pdf",
        "doc_note": "Attached: Tier-1 automotive cross-border freight manifest"
    },

    # Sales Queue
    {
        "id": "meet_sales_01",
        "title": "Sunbelt Logistics LLC — Freight Factoring & Cash Flow Review",
        "source": "Google Meet via Fireflies.ai",
        "received_ago": "22 mins ago",
        "type": "sales",
        "entity": "Sunbelt Logistics LLC (Phoenix, AZ)",
        "contact": "Marcus Vance (Managing Director)",
        "headline": "$2.4M ARR | 14 Tractor Fleet",
        "lead_data": BENCHMARK_SALES_LEAD,
        "default_doc_url": "https://example.com/freight/sunbelt-broker-aging.pdf",
        "doc_note": "Attached AR Aging Report: 60-day outstanding broker freight bills ($140,000 USD)"
    },
    {
        "id": "meet_sales_02",
        "title": "Baja Cross-Border Cold Chain — AR Aging & Perishables Financing",
        "source": "Google Meet via Read AI",
        "received_ago": "1 hour ago",
        "type": "sales",
        "entity": "Baja Cross-Border Cold Chain (Otay Mesa, CA)",
        "contact": "Diana Navarro (VP Operations)",
        "headline": "$1.6M ARR | 8 Refrigerated Reefers",
        "lead_data": BAJA_SALES_LEAD,
        "default_doc_url": "https://example.com/freight/baja-cold-chain-ar-aging.pdf",
        "doc_note": "Attached AR Aging: Perishables produce broker bills"
    },
    {
        "id": "meet_sales_03",
        "title": "Alamo Industrial Coatings — Commercial Progress Billing Line",
        "source": "Google Meet via Read AI",
        "received_ago": "4 hours ago",
        "type": "sales",
        "entity": "Alamo Industrial Coatings (San Antonio, TX)",
        "contact": "Jorge Villarreal (Owner)",
        "headline": "$980,000 ARR | Municipal Painting",
        "lead_data": ALAMO_SALES_LEAD,
        "default_doc_url": "https://example.com/contracts/saws-water-tank-billing.pdf",
        "doc_note": "Attached: San Antonio Water System municipal contract"
    },

    # HR Queue
    {
        "id": "meet_hr_01",
        "title": "Sofia Valdez — Senior Bilingual Credit Analyst Screening",
        "source": "Google Meet via Read AI",
        "received_ago": "35 mins ago",
        "type": "hr",
        "entity": "Sofia Valdez (Mazatlán, Sin.)",
        "contact": "Elena Ramos (Interviewer)",
        "headline": "Senior Bilingual Credit Analyst (C1)",
        "transcript": BENCHMARK_HR_TRANSCRIPT,
        "default_doc_url": "https://example.com/resumes/sofia-valdez-underwriter.pdf",
        "doc_note": "Attached Resume & C1 Language Certificate (Cambridge CEFR)"
    },
    {
        "id": "meet_hr_02",
        "title": "Carlos Mendoza — Commercial BDR (Logistics) Screening",
        "source": "Google Meet via Read AI",
        "received_ago": "2 hours ago",
        "type": "hr",
        "entity": "Carlos Mendoza (Mazatlán, Sin.)",
        "contact": "Elena Ramos (Interviewer)",
        "headline": "Commercial BDR (Logistics) (B2+)",
        "transcript": CARLOS_MENDOZA_TRANSCRIPT,
        "default_doc_url": "https://example.com/resumes/carlos-mendoza-bdr.pdf",
        "doc_note": "Attached Resume: 3 years freight broker outbound sales"
    },
    {
        "id": "meet_hr_03",
        "title": "Valeria Beltrán — Senior Talent Acquisition Specialist Screening",
        "source": "Google Meet via Fireflies.ai",
        "received_ago": "6 hours ago",
        "type": "hr",
        "entity": "Valeria Beltrán (Culiacán, Sin.)",
        "contact": "Elena Ramos (Interviewer)",
        "headline": "Senior Talent Acquisition Specialist (C1)",
        "transcript": VALERIA_BELTRAN_TRANSCRIPT,
        "default_doc_url": "https://example.com/resumes/valeria-beltran-recruiter.pdf",
        "doc_note": "Attached Resume: 5 years financial services recruiting"
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


def get_item_by_id(item_id: str) -> Dict[str, Any]:
    for item in INCOMING_MEETINGS_QUEUE:
        if item["id"] == item_id:
            return item
    return INCOMING_MEETINGS_QUEUE[0]
