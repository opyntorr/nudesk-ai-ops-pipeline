from typing import List, Literal
from pydantic import BaseModel, Field


class AsanaTask(BaseModel):
    task_title: str = Field(description="Actionable task title for team members")
    priority: Literal["High", "Medium", "Low"] = Field(description="Task urgency priority")
    assignee_role: Literal["Credit Analyst", "Compliance Officer", "Underwriting Lead", "BDR"] = Field(
        description="Operational role assigned to this task"
    )


class CreditTriageOutput(BaseModel):
    applicant_name: str = Field(description="Full name of the primary contact or business owner")
    business_name: str = Field(description="Legal or commercial business name")
    industry: str = Field(description="Industry sector of the business")
    loan_amount_requested_usd: float = Field(description="Total requested loan amount in USD")
    stated_monthly_revenue_usd: float = Field(description="Stated or verified monthly gross revenue in USD")
    estimated_dti_ratio: float = Field(
        description="Estimated Debt-to-Income or debt service ratio as a decimal (e.g. 0.35 for 35%)"
    )
    risk_tier: Literal["Low Risk", "Moderate Risk", "High Risk"] = Field(
        description="Overall credit underwriting risk assessment tier"
    )
    executive_summary: str = Field(
        description="Concise 2-4 sentence executive overview of the business, financial standing, and capital need"
    )
    red_flags: List[str] = Field(
        description="Key risks identified during discovery call (e.g. tax liens, cash flow volatility, short history)"
    )
    asana_tasks: List[AsanaTask] = Field(
        description="Standard operating tasks created for the credit and underwriting teams"
    )


class SalesLeadOutput(BaseModel):
    company_name: str = Field(description="Target prospective company name")
    contact_person: str = Field(description="Primary decision maker name and title")
    industry: str = Field(description="Business industry classification")
    annual_revenue_usd: float = Field(description="Estimated or reported annual revenue in USD")
    funding_intent: str = Field(description="Stated purpose for seeking commercial financing or factoring")
    lead_score: int = Field(
        description="Lead qualification score from 1 to 100 based on fit, ticket size, and urgency",
        ge=1,
        le=100
    )
    score_rationale: str = Field(description="Clear explanation of the score drivers and qualification fit")
    cold_email_en: str = Field(
        description="Subject line and high-converting personalized cold email body in professional US business English"
    )
    phone_script_30s_en: str = Field(
        description="Persuasive 30-second cold calling opening script for the Mazatlan BDR team"
    )


class HRTalentOutput(BaseModel):
    candidate_name: str = Field(description="Full name of candidate interviewed")
    applied_role: str = Field(description="Role applied for within nuDesk or lending client team")
    application_area: Literal[
        "Credit Underwriting & Risk",
        "Commercial Sales & BDR",
        "Operations & Accounting",
        "Technology & Systems"
    ] = Field(
        default="Credit Underwriting & Risk",
        description="Functional operational area within the financial services hub"
    )
    candidate_fit_tier: Literal["High Fit", "Moderate Fit", "Low Fit"] = Field(
        default="High Fit",
        description="Qualitative AI evaluation tier of overall candidate suitability for the role and culture"
    )
    candidate_fit_score: int = Field(
        default=88,
        description="Qualitative candidate fit evaluation score from 1 to 100",
        ge=1,
        le=100
    )
    psychometrics_score: int = Field(
        default=85,
        description="Calificación de pruebas psicométricas y perfil de personalidad laboral (0 a 100)",
        ge=0,
        le=100
    )
    knowledge_test_score: int = Field(
        default=85,
        description="Calificación en test técnico de conocimientos específicos del área financiera (0 a 100)",
        ge=0,
        le=100
    )
    overall_fit_score: int = Field(
        default=88,
        description="Composite fit score (1 to 100) assessing technical capability, fluency, and culture fit",
        ge=1,
        le=100
    )
    bilingual_fluency_rating: Literal[
        "C2 Native / Bilingual",
        "C1 Advanced Professional",
        "B2 Working Proficiency",
        "Below Target"
    ] = Field(
        default="C1 Advanced Professional",
        description="Assessed English fluency for US lending communication"
    )
    executive_summary: str = Field(
        description="2-3 sentence overview of candidate strengths, background fit, and communication style"
    )
    technical_competencies: List[str] = Field(
        description="Core skills verified during screening (e.g. credit memo drafting, DSCR, Google Workspace)"
    )
    behavioral_red_flags: List[str] = Field(
        description="Potential concerns or risks identified during interview (e.g. short tenures, evasive answers)"
    )
    recommended_action: Literal[
        "Advance to Hiring Manager",
        "Hold for Alternate Pipeline",
        "Polite Reject"
    ] = Field(description="Next operational step for the recruiting pipeline")
    next_interview_focus_questions: List[str] = Field(
        description="Key follow-up questions for the Hiring Manager to drill down into during next round"
    )

