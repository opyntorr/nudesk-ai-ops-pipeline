from models import AsanaTask, CreditTriageOutput, SalesLeadOutput

MOCK_FIREFLIES_TRANSCRIPT = """[00:00:02] Agent (nuDesk Discovery): Thank you for taking the time today, Robert. I want to quickly review your commercial financing inquiry for Apex Fleet Repair.
[00:00:10] Robert Martinez: Sure thing. As I mentioned in the online form, we're located in Dallas, Texas. We operate a heavy-duty commercial truck repair bay.
[00:00:22] Agent: Great. What is the requested loan amount and the core capital use?
[00:00:27] Robert Martinez: We are seeking $85,000 USD to acquire two high-capacity hydraulic lift diagnostics systems. We have high customer demand from fleet accounts, but our current equipment bottlenecks our turnaround times.
[00:00:41] Agent: Understood. What does your current monthly gross revenue look like over the last 6 months?
[00:00:48] Robert Martinez: We consistently average around $38,000 USD per month in gross billings. Summer was slightly higher at $42,000.
[00:00:58] Agent: Perfect. And what about existing commercial debts or daily/weekly payment balances?
[00:01:05] Robert Martinez: We have an existing equipment lease with about $14,000 balance remaining, paying around $1,200 monthly. No merchant cash advances or high-interest daily loans.
[00:01:17] Agent: Any public records, pending bankruptcies, or federal tax issues we should be aware of before pull?
[00:01:25] Robert Martinez: To be completely transparent, we have an IRS tax lien from the 2023 fiscal year for about $18,500. However, we entered into an official IRS installment agreement six months ago, and we have made every payment on time with direct debit proof.
[00:01:45] Agent: Thank you for disclosing that upfront, Robert. Having a formal installment agreement in good standing makes a big difference for our credit committee.
[00:01:54] Robert Martinez: Good to hear. I can email over the last 4 months of business bank statements and the IRS letter today.
[00:02:04] Agent: Excellent. We will initiate the formal triage file and schedule underwriting review right away."""


MOCK_SALES_LEAD_RAW = """Company: Sunbelt Logistics LLC
Headquarters: Phoenix, Arizona
Primary Contact: Marcus Vance (Managing Partner / Operations VP)
Email: mvance@sunbeltlogistics-demo.com
Phone: +1 (602) 555-0184
Fleet Size: 14 Class-8 Freightliner tractors with refrigerated reefers
Annual Gross Revenue: $2,400,000 USD
Current Operating Challenge: Experiencing severe working capital strain due to freight brokerage payment terms extending from 30 to 60 days. Fuel, maintenance, and driver payroll are due weekly.
Financing Intent: Looking for a dedicated non-recourse Invoice Factoring facility of $250,000 - $350,000 USD credit line to accelerate cash flow on completed freight bills.
Timeline: Immediate (needs funding facility active within 10 business days)."""


MOCK_FALLBACK_CREDIT = CreditTriageOutput(
    applicant_name="Robert Martinez",
    business_name="Apex Fleet Repair",
    industry="Commercial Heavy-Duty Automotive Services",
    loan_amount_requested_usd=85000.0,
    stated_monthly_revenue_usd=38000.0,
    estimated_dti_ratio=0.32,
    risk_tier="Moderate Risk",
    executive_summary="Apex Fleet Repair is an established commercial truck repair facility in Dallas, TX generating $38,000 USD monthly revenue. The borrower requests $85,000 USD for revenue-generating hydraulic diagnostics equipment with strong fleet account demand. The profile is fundamentally viable but requires verification of public records.",
    red_flags=[
        "Active federal tax lien of $18,500 USD from FY2023 on record",
        "Existing equipment lease obligation of $1,200/month ($14,000 outstanding balance)",
        "Documentation needed: Formal IRS installment agreement verification and 6 months proof of debits"
    ],
    asana_tasks=[
        AsanaTask(
            task_title="Verify IRS Installment Agreement Letter and 6 Months On-Time Payment Records",
            priority="High",
            assignee_role="Compliance Officer"
        ),
        AsanaTask(
            task_title="Audit Last 4 Months Commercial Bank Statements for Deposit Consistency",
            priority="High",
            assignee_role="Credit Analyst"
        ),
        AsanaTask(
            task_title="Verify Equipment Quote and Vendor Invoice for $85k Hydraulic Systems",
            priority="Medium",
            assignee_role="Credit Analyst"
        ),
        AsanaTask(
            task_title="Run Secretary of State UCC-1 Lien Search (Dallas County, TX)",
            priority="Medium",
            assignee_role="Compliance Officer"
        )
    ]
)


MOCK_FALLBACK_SALES = SalesLeadOutput(
    company_name="Sunbelt Logistics LLC",
    contact_person="Marcus Vance (Managing Partner / Operations VP)",
    industry="Freight & Logistics (Refrigerated Transport)",
    annual_revenue_usd=2400000.0,
    funding_intent="Immediate Invoice Factoring line ($250k - $350k) to bridge 60-day freight broker receivables and protect driver payroll.",
    lead_score=88,
    score_rationale="High-urgency commercial profile with $2.4M annual revenue and strong tangible collateral (verified freight bills). Urgent working capital requirement driven by standard broker terms (60 days) makes factoring the ideal financial product with minimal acquisition resistance.",
    cold_email_en="""Subject: Marcus -- accelerating Sunbelt's 60-day broker invoices before payroll

Hi Marcus,

Running a 14-tractor reefer fleet in Phoenix means fuel and driver compensation hit your accounts every Friday, while freight brokers sit on your invoices for 45 to 60 days.

At nuDesk Capital, we partner directly with growing regional fleets to turn outstanding freight bills into immediate same-day liquidity without restrictive bank covenants or personal real estate liens.

We can establish a competitive non-recourse factoring line ($250k-$350k) within 5 business days, giving you immediate cash flow predictability as you add lanes.

Do you have 7 minutes this Thursday at 10:00 AM MST for a quick feasibility check?

Best regards,

DeskMate Sales Acceleration Team | nuDesk Operations
Mazatlan Talent Hub -- US Lending Operations""",
    phone_script_30s_en="""Hi Marcus, this is [BDR Name] with nuDesk Capital. I'll be brief -- I see Sunbelt is running 14 reefers out of Phoenix. 

Most fleet operators we work with in the Southwest are facing broker payment delays stretching to 60 days, which chokes payroll and fuel cash flow. 

We provide same-day freight bill advances with zero long-term lockups so your trucks stay moving. 

Marcus, if I could show you how to unlock your current unpaid receivables by this Friday, would you be open to a 5-minute review tomorrow morning?"""
)
