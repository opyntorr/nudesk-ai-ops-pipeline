# Agentic Architecture & AI Pairing Directives (AGENTS.md)
### nuDesk Operations Studio | FinTech Operational Cockpit

This repository is architected for seamless collaboration between bilingual operations specialists and autonomous AI agents (specifically **Claude Code** and **Gemini Antigravity**).

---

## 1. The Cyborg Organization Model

nuDesk pairs human operational specialists in Mazatlán, Sinaloa with domain-trained AI agents to eliminate manual backoffice overhead in commercial lending, BDR prospecting, and bilingual talent screening.

Instead of unguided, open-ended conversational generation, the AI engine operates under **Harness Engineering**:
- The LLM is an interchangeable inference engine (Google Gemini cascade: `gemini-3.5-flash-lite`, `gemini-3.5-flash`, `gemini-1.5-pro`).
- Deterministic tools execute mathematical calculations and database queries outside the LLM context.
- Output formats are governed by strict Pydantic V2 contracts.
- System state is persisted in an SQLite audit trail with active SLA tracking.

---

## 2. Deterministic Grounding & Anti-Hallucination Rules

When acting as an operational underwriter or agent co-pilot, the following rules are strictly enforced:

1. **Zero Numerical Hallucinations in Debt Ratios:**
   - An LLM must NEVER perform mental arithmetic or estimate Debt-to-Income (DTI) or Debt Service Coverage Ratios (DSCR).
   - The agent MUST invoke `tool_compute_financial_ratios` with verified gross revenue and requested principal to obtain the mathematical ratio and risk tier.
2. **Mandatory Historical Pre-Check:**
   - Before synthesizing an underwriting memo, the agent MUST invoke `tool_lookup_applicant_history` to query `operations_history.db` for prior applications or duplicate records.
3. **Pydantic Schema Compliance:**
   - All responses must validate against `CreditTriageOutput`, `SalesLeadOutput`, or `HRTalentOutput` defined in `models.py`.
4. **Zero-Config Fallback Guarantees:**
   - When external LLM APIs are unreachable or unconfigured, the agent harness MUST fall back to pre-computed benchmark records without throwing unhandled exceptions.

---

## 3. Registered Tool Catalog

Tool specifications are formally defined in `agent_specs/tools_manifest.json`:

| Tool Name | Module | Purpose |
|---|---|---|
| `tool_lookup_applicant_history` | `ai_engine.py` | Queries SQLite for historical credit records and red flags |
| `tool_compute_financial_ratios` | `ai_engine.py` | Deterministic calculation of exact DSCR, DTI, and risk tier |
| `tool_inbound_api_ingest` | `inbound_api.py` | HTTP ingestion server (:8502) receiving Google Sheets & n8n streams |
| `tool_dispatch_to_n8n` | `crm_dispatcher.py` | Authenticated webhook dispatcher (:5678) with `X-nuDesk-Auth-Token` |

---

## 4. Multi-Step Agent Execution Loop

The autonomous credit triage loop (`agentic_credit_triage`) executes the following sequential steps:

```text
[Raw Call Transcript / Voice Note]
       │
       ▼
[Step 1: Check Database History]
       │ Tool: tool_lookup_applicant_history(business_name)
       │ Returns: Historical records and prior red flags from SQLite
       ▼
[Step 2: Deterministic Ratio Computation]
       │ Tool: tool_compute_financial_ratios(revenue, debt, amount)
       │ Returns: Exact DSCR ratio, DTI percentage, and deterministic risk tier
       ▼
[Step 3: Grounded Pydantic Synthesis]
       │ Model: Gemini 3.5 Flash-Lite (with Tool Grounding)
       │ Injects: Calculated ratios + Historical records into system context
       ▼
[Structured Credit Dossier + Asana Tasks]
```

Every execution produces an inspectable `Agent Reasoning & Deterministic Tool Execution Trace` rendered in the UI and stored in the audit log.

---

---

## 5. Enterprise Agent Guardrails & Interceptors (agent_guardrails.py)

To ensure enterprise-grade safety and zero-drift execution, all agent interactions pass through pre-flight and post-flight interceptors:

1. **Pre-Flight Privacy & Security Interceptors:**
   - **Confidential PII Masking:** Regex-based sanitization automatically redacts US Social Security Numbers (`[REDACTED_SSN]`), Employer Identification Numbers (`[REDACTED_EIN]`), and corporate payment card numbers before sending raw transcripts to model contexts.
   - **Adversarial Prompt Injection Defense:** Detects and flags jailbreak signatures, system override attempts, and instruction subversions, automatically routing compromised transcripts to High Risk quarantine and injecting security alerts into underwriting red flags.

2. **Post-Flight Mathematical Reconciliation Interceptors:**
   - **Ground Truth Fact-Checking:** Compares the LLM's synthesized DTI against `tool_compute_financial_ratios`. If the synthesized DTI drifts by more than 15 percentage points, the harness overrides the value with mathematical ground truth.
   - **Mandatory Compliance Enforcement:** Guarantees that every triaged credit file contains standard KYC/AML compliance verification tasks in Asana.

---

## 6. Continuous Agent Evaluation & Benchmarking Harness (evals/)

The repository includes an autonomous evaluation harness (`evals/agent_eval_harness.py`) that benchmarks agent performance across 6 operational scenarios:

```bash
make eval
```

Evaluation Battery:
1. **Prime Credit File:** Evaluates clean multi-tool execution and accurate DTI calculation.
2. **Distressed Debt Burden:** Asserts post-flight guardrail overrides conflicting risk tiers.
3. **Historical DB Lookup:** Asserts SQLite tool queries prior applicant default records.
4. **Prompt Injection Attack:** Asserts adversarial subversion is trapped and flagged.
5. **PII Masking:** Asserts SSNs, EINs, and cards are redacted prior to inference.
6. **Zero-Config Resilience:** Asserts offline benchmark fallback executes without exceptions.

Target: **100.0% Harness Safety & Grounding Score (Grade: A+)**.

---

## 7. Development & Testing Protocol for AI Agents

When developing or modifying code in this repository:
1. **Never use emojis** in code, comments, commit messages, or documentation.
2. **Never run `colcon build`**.
3. **Validate 100% Test Passing:** Always verify `make test` passes all 82 automated unit tests.
4. **Validate Agent Benchmarks:** Always verify `make eval` passes all 6 evaluation scenarios (100% score).
5. **Verify Headless Execution:** Verify `streamlit.testing.v1.AppTest` executes without unhandled runtime exceptions.
6. **Verify E2E Rendering:** Run `scripts/e2e_playwright_audit.py` to confirm full-page rendering and screenshot synchronization across Light and Dark mode.
