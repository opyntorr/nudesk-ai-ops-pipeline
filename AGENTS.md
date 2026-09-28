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

## 5. Development & Testing Protocol for AI Agents

When developing or modifying code in this repository:
1. **Never use emojis** in code, comments, commit messages, or documentation.
2. **Never run `colcon build`**.
3. **Validate 100% Test Passing:** Always verify `make test` passes all 78 automated unit tests.
4. **Verify Headless Execution:** Verify `streamlit.testing.v1.AppTest` executes without unhandled runtime exceptions.
5. **Verify E2E Rendering:** Run `scripts/e2e_playwright_audit.py` to confirm full-page rendering and screenshot synchronization across Light and Dark mode.
