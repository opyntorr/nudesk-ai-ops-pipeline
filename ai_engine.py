import os
import json
from typing import Tuple, Optional, List
from dotenv import load_dotenv

from models import CreditTriageOutput, SalesLeadOutput, HRTalentOutput
from mock_data import MOCK_FALLBACK_CREDIT, MOCK_FALLBACK_SALES, MOCK_FALLBACK_HR

load_dotenv()

# Prioritized list of active Google Gemini models to handle transient demand spikes
CANDIDATE_MODELS: List[str] = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-flash-latest",
    "gemini-3.8-flash"
]


def _get_api_key(explicit_key: Optional[str] = None) -> Optional[str]:
    """Retrieve API key from explicit argument or environment variable."""
    if explicit_key and explicit_key.strip():
        return explicit_key.strip()
    env_key = os.getenv("GEMINI_API_KEY", "")
    return env_key.strip() if env_key else None


def analyze_credit_call(
    transcript: str,
    api_key: Optional[str] = None,
    supplementary_doc: str = ""
) -> Tuple[CreditTriageOutput, bool, Optional[str]]:
    """
    Parse a raw discovery call transcript into a structured CreditTriageOutput.
    Tries candidate Gemini models sequentially, falling back to benchmark data if needed.
    Returns: (output_object, is_fallback, status_or_error_message)
    """
    effective_key = _get_api_key(api_key)

    if not effective_key:
        return (
            MOCK_FALLBACK_CREDIT,
            True,
            "DEMONSTRATION MODE: Displaying pre-computed benchmark analysis. To analyze dynamic or custom transcripts in real time, please input a Google Gemini API key in the sidebar."
        )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=effective_key)

        doc_section = ""
        if supplementary_doc and supplementary_doc.strip():
            doc_section = f"""
SUPPLEMENTARY ATTACHED DOCUMENTS / WEB LINK DATA:
\"\"\"
{supplementary_doc.strip()}
\"\"\"
Reconcile and incorporate these supplementary facts with the call transcript.
"""

        prompt = f"""You are an elite Senior Commercial Credit Underwriter at nuDesk Capital.
Analyze the following post-call discovery transcript from our Fireflies / dialer system.
Extract all relevant applicant details, compute risk tier (Low Risk, Moderate Risk, High Risk),
estimate the DTI ratio, list clear red flags, and generate actionable operational tasks for Asana.

TRANSCRIPT:
\"\"\"
{transcript}
\"\"\"
{doc_section}
Return strictly valid JSON matching the requested CreditTriageOutput schema.
"""


        last_error = None
        for model_name in CANDIDATE_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=CreditTriageOutput,
                        temperature=0.2
                    )
                )

                raw_text = response.text
                parsed_dict = json.loads(raw_text)
                result = CreditTriageOutput(**parsed_dict)
                return (result, False, f"Live inference generated using {model_name}.")
            except Exception as model_err:
                last_error = model_err
                continue

        err_str = f"Live inference reached capacity on candidate models ({type(last_error).__name__}). Showing benchmark analysis."
        return (MOCK_FALLBACK_CREDIT, True, err_str)

    except Exception as exc:
        err_str = f"Initialization error ({type(exc).__name__}: {str(exc)}). Switched to Demonstration Mode."
        return (MOCK_FALLBACK_CREDIT, True, err_str)


def qualify_sales_lead(
    lead_info: str,
    api_key: Optional[str] = None,
    supplementary_doc: str = ""
) -> Tuple[SalesLeadOutput, bool, Optional[str]]:
    """
    Qualify an inbound/outbound commercial prospect and generate tailored outreach assets.
    Tries candidate Gemini models sequentially, falling back to benchmark data if needed.
    Returns: (output_object, is_fallback, status_or_error_message)
    """
    effective_key = _get_api_key(api_key)

    if not effective_key:
        return (
            MOCK_FALLBACK_SALES,
            True,
            "DEMONSTRATION MODE: Displaying pre-computed benchmark analysis. To score dynamic or custom sales leads in real time, please input a Google Gemini API key in the sidebar."
        )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=effective_key)

        doc_section = ""
        if supplementary_doc and supplementary_doc.strip():
            doc_section = f"""
SUPPLEMENTARY ATTACHED DOCUMENTS / WEB LINK DATA:
\"\"\"
{supplementary_doc.strip()}
\"\"\"
Incorporate these verified collateral/aging details into the score and outreach rationale.
"""

        prompt = f"""You are an expert Head of Growth & Lead Scoring Architect at nuDesk Capital.
Evaluate the following business commercial profile for financial viability, factoring, or commercial lending.
Score the lead from 1 to 100 based on transaction size, operational urgency, and revenue strength.
Write an authentic, highly persuasive cold email in professional US business English, and draft a punchy
30-second telephone script for our bilingual BDR team in Mazatlan.

PROSPECT DATA:
\"\"\"
{lead_info}
\"\"\"
{doc_section}
Return strictly valid JSON matching the requested SalesLeadOutput schema.
"""

        last_error = None
        for model_name in CANDIDATE_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=SalesLeadOutput,
                        temperature=0.3
                    )
                )

                raw_text = response.text
                parsed_dict = json.loads(raw_text)
                result = SalesLeadOutput(**parsed_dict)
                return (result, False, f"Live inference generated using {model_name}.")
            except Exception as model_err:
                last_error = model_err
                continue

        err_str = f"Live inference reached capacity on candidate models ({type(last_error).__name__}). Showing benchmark analysis."
        return (MOCK_FALLBACK_SALES, True, err_str)

    except Exception as exc:
        err_str = f"Initialization error ({type(exc).__name__}: {str(exc)}). Switched to Demonstration Mode."
        return (MOCK_FALLBACK_SALES, True, err_str)


def analyze_hr_interview(
    interview_transcript: str,
    api_key: Optional[str] = None,
    supplementary_doc: str = ""
) -> Tuple[HRTalentOutput, bool, Optional[str]]:
    """
    Analyze an HR screening interview transcript (Read AI / Google Meet) for FinServ talent.
    Evaluates bilingual fluency, technical competencies, and next round recommendations.
    Returns: (output_object, is_fallback, status_or_error_message)
    """
    effective_key = _get_api_key(api_key)

    if not effective_key:
        return (
            MOCK_FALLBACK_HR,
            True,
            "DEMONSTRATION MODE: Displaying pre-computed benchmark analysis. To analyze dynamic candidate interviews in real time, please input a Google Gemini API key in IT settings."
        )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=effective_key)

        doc_section = ""
        if supplementary_doc and supplementary_doc.strip():
            doc_section = f"""
CANDIDATE RESUME / CERTIFICATES / WORK SAMPLES:
\"\"\"
{supplementary_doc.strip()}
\"\"\"
Cross-reference the interview claims with these resume credentials.
"""

        prompt = f"""You are a Lead Talent Assessment Officer at nuDesk MX in Mazatlan, Sinaloa.
We recruit and train bilingual financial services analysts, underwriters, and BDRs for US financial institutions.
Analyze the following candidate screening interview transcript (captured via Read AI in Google Meet).
Evaluate the candidate's technical skills, bilingual communication fluency, red flags, and determine whether
to advance them to the Hiring Manager round. Formulate 3 sharp case-study questions for the next round.

INTERVIEW TRANSCRIPT:
\"\"\"
{interview_transcript}
\"\"\"
{doc_section}
Return strictly valid JSON matching the requested HRTalentOutput schema.
"""

        last_error = None
        for model_name in CANDIDATE_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=HRTalentOutput,
                        temperature=0.2
                    )
                )

                raw_text = response.text
                parsed_dict = json.loads(raw_text)
                result = HRTalentOutput(**parsed_dict)
                return (result, False, f"Live inference generated using {model_name}.")
            except Exception as model_err:
                last_error = model_err
                continue

        err_str = f"Live inference reached capacity on candidate models ({type(last_error).__name__}). Showing benchmark analysis."
        return (MOCK_FALLBACK_HR, True, err_str)

    except Exception as exc:
        err_str = f"Initialization error ({type(exc).__name__}: {str(exc)}). Switched to Demonstration Mode."
        return (MOCK_FALLBACK_HR, True, err_str)

