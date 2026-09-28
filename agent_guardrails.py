#!/usr/bin/env python3
"""
nuDesk AI Agent Guardrails & Pre/Post-Flight Interceptors
Enforces enterprise security, PII privacy masking, prompt injection defense,
and post-flight deterministic mathematical reconciliation on LLM responses.
"""
import re
from typing import Tuple, List, Dict, Any, Optional
from models import CreditTriageOutput, AsanaTask

# PII Detection Regexes
RE_SSN = re.compile(r"\b\d{3}[- ]\d{2}[- ]\d{4}\b")
RE_EIN = re.compile(r"\b\d{2}[-]\d{7}\b")
RE_CARD = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")

# Prompt Injection Threat Signatures
INJECTION_SIGNATURES = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions?",
    r"disregard\s+(all\s+)?(rules|guidelines|safeguards)",
    r"system\s+(prompt\s+)?override",
    r"you\s+are\s+now\s+(in\s+)?(developer|dan|god|unrestricted)\s+mode",
    r"bypass\s+(all\s+)?(checks|validation|underwriting)",
    r"approve\s+(this\s+)?(loan|lead|candidate)\s+with(out)?\s+any\s+checks?",
    r"do\s+not\s+call\s+tools?",
    r"jailbreak"
]
COMPILED_INJECTIONS = [re.compile(sig, re.IGNORECASE) for sig in INJECTION_SIGNATURES]


def mask_sensitive_pii(text: str) -> Tuple[str, List[str]]:
    """
    Pre-flight Guardrail: Redact SSNs, EINs, and Credit Cards from text
    prior to sending to LLM context to safeguard confidential financial data.
    Returns: (sanitized_text, list_of_redacted_categories)
    """
    if not text:
        return "", []

    redacted_categories = []
    sanitized = text

    if RE_SSN.search(sanitized):
        sanitized = RE_SSN.sub("[REDACTED_SSN]", sanitized)
        redacted_categories.append("SSN")

    if RE_EIN.search(sanitized):
        sanitized = RE_EIN.sub("[REDACTED_EIN]", sanitized)
        redacted_categories.append("EIN")

    if RE_CARD.search(sanitized):
        sanitized = RE_CARD.sub("[REDACTED_PAYMENT_CARD]", sanitized)
        redacted_categories.append("CreditCard")

    return sanitized, redacted_categories


def detect_prompt_injection(text: str) -> Tuple[bool, str, List[str]]:
    """
    Pre-flight Guardrail: Scan incoming transcripts for prompt injection,
    jailbreak payloads, or instructions attempting to subvert underwriting logic.
    Returns: (is_threat, threat_summary, matched_patterns)
    """
    if not text:
        return False, "Clean", []

    matched = []
    for pattern in COMPILED_INJECTIONS:
        if pattern.search(text):
            matched.append(pattern.pattern)

    if matched:
        summary = f"Adversarial Prompt Injection Detected ({len(matched)} match pattern[s]). Subversion attempt blocked."
        return True, summary, matched

    return False, "No injection detected", []


def reconcile_deterministic_ratios(
    memo: CreditTriageOutput,
    ratios: Dict[str, Any]
) -> Tuple[CreditTriageOutput, bool, str]:
    """
    Post-flight Guardrail: Cross-checks LLM synthesized DTI and risk tier against
    the mathematically computed tool output. If the LLM drifts significantly
    or contradicts the mathematical ground truth, enforces deterministic override.
    Returns: (reconciled_memo, was_overridden, rationale)
    """
    if "dti_ratio" not in ratios:
        return memo, False, "No deterministic ratios available to cross-check."

    computed_dti = float(ratios["dti_ratio"])
    computed_risk = ratios.get("deterministic_risk_tier", memo.risk_tier)

    # Check for DTI divergence greater than 15 percentage points
    discrepancy = abs(memo.estimated_dti_ratio - computed_dti)
    was_overridden = False
    reconciliation_notes = []

    if discrepancy > 0.15:
        reconciliation_notes.append(
            f"Overrode LLM DTI ({memo.estimated_dti_ratio:.1%}) with verified mathematical ground truth ({computed_dti:.1%})."
        )
        memo.estimated_dti_ratio = round(computed_dti, 4)
        was_overridden = True

    # If the mathematical calculation flagged High Risk, the memo cannot downgrade to Low Risk
    if computed_risk == "High Risk" and memo.risk_tier == "Low Risk":
        reconciliation_notes.append("Elevated risk tier from Low Risk to High Risk based on deterministic debt coverage breach.")
        memo.risk_tier = "High Risk"
        was_overridden = True

    # Ensure standard KYC Asana task is present
    has_kyc_task = any("kyc" in t.task_title.lower() or "compliance" in t.task_title.lower() for t in memo.asana_tasks)
    if not has_kyc_task:
        memo.asana_tasks.append(
            AsanaTask(
                task_title="Verify borrower identification and execute standard KYC compliance check",
                priority="High",
                assignee_role="Compliance Officer"
            )
        )
        reconciliation_notes.append("Appended mandatory compliance KYC Asana task.")

    rationale = " ".join(reconciliation_notes) if reconciliation_notes else "Post-flight validation passed; LLM output conforms to mathematical ground truth."
    return memo, was_overridden, rationale
