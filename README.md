# nuDesk Operations Studio
### AI-Powered Credit Triage & Sales Acceleration Engine for Financial Services (FinServ)
**nuDesk MX Technical Assessment | Candidate: Christian Omar Payán Torróntegui**

[![nuDesk Ops Studio CI Pipeline](https://github.com/opyntorr/nudesk-ai-ops-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/opyntorr/nudesk-ai-ops-pipeline/actions/workflows/ci.yml)

---

## 1. Executive Summary & Business Context

At **nuDesk MX**, operational teams in Mazatlán, Sinaloa partner with US commercial lenders, regional banks, and factoring firms to streamline debt origination, sales outreach, and underwriting workflows. 

Traditional BPOs scale operational capacity by linearly increasing headcount ("seat count"), resulting in high overhead, employee fatigue on manual data entry, and delayed turnaround times. nuDesk disrupts this paradigm through the **Cyborg Organization Model**: pairing bilingual human specialists with domain-trained AI agents to multiply productivity while safeguarding credit compliance.

**nuDesk Operations Studio** is an enterprise-ready prototype designed to eliminate the two most common operational bottlenecks faced by nuDesk teams:

1. **Credit Operations (Post-Call Discovery Triage):**
   - **The Problem:** Loan officers and discovery agents conduct 15-to-30 minute calls with US business owners. Manually listening to recordings or reading transcripts to extract financial parameters (debt, revenue, equipment quotes, tax liens) and creating underwriting tickets takes 40+ minutes per file.
   - **The Solution:** Ingests raw call transcripts (from dialers or Fireflies.ai), extracts key financial variables into strict Pydantic JSON schemas, computes an initial risk tier (Low, Moderate, High), isolates underwriting red flags, and automatically generates prioritized action items for the underwriting team (Asana-ready).

2. **Sales Operations (BDR Lead Scoring & Rapid Outreach):**
   - **The Problem:** Business Development Representatives (BDRs) in Mazatlán prospecting US logistics, construction, and manufacturing companies must manually research company viability, assess working capital fit, and draft custom outreach messages.
   - **The Solution:** Ingests raw commercial prospect profiles, computes a lead score from 1 to 100 based on urgency and collateral viability, provides clear underwriting rationale, and generates both an executive cold email draft and a 30-second telephone pitch tailored for high-conversion speed-to-lead dialing.

3. **HR Solutions (Bilingual Talent Screening):**
   - **The Problem:** Vetting high-volume candidate interviews for English fluency, commercial empathy, and debt qualification skills requires hours of interview review.
   - **The Solution:** Evaluates CEFR fluency, scores cultural competencies, identifies candidate red flags, and drafts targeted behavioral probing questions for hiring managers.

4. **Enterprise Dispatch & Hyperautomation (n8n & Google Workspace):**
   - Validated data structures are dispatched via HTTP POST webhooks to a local **n8n** orchestration engine (running in Docker), which routes and persists data into Google Sheets (acting as a live CRM/Pipeline tracker) and stages email drafts.

---

## 2. Architectural Highlights & "Harness Engineering"

A foundational principle of this project is **Model-Agnostic Architecture**. 

Large Language Models (LLMs) are evolving at rapid speed. Designing business software directly coupled to a specific model creates brittle systems vulnerable to API deprecation or vendor lock-in. 

In this application, the LLM is treated strictly as an interchangeable inference engine. The permanent enterprise value resides in the **Harness**:
- **Strict Data Contracts:** Pydantic schemas enforce type safety and structure at compile and runtime.
- **Fail-Safe Fallback:** If an API key is absent, expired, or rate-limited, the application gracefully transitions to Demonstration Mode, providing realistic synthetic records without throwing runtime exceptions.
- **Decoupled Orchestration:** Workflow routing, data transformation, and CRM synchronization are handled by n8n, ensuring that changes to downstream destinations (e.g. migrating from Google Sheets to HubSpot or Salesforce) require zero changes to the core AI engine.
- **Google Cloud Console OAuth 2.0 & RBAC:** Live Google Workspace Single Sign-On paired with granular role-based access control, isolating sensitive IT configurations from non-technical operators.
- **Design System & Theme Engine:** WCAG AAA high-contrast minimalist Light Mode default with an instant Dark Mode toggle, styled to match nuDesk brand tokens.

```text
+-----------------------------------------------------------------------------------+
|                           nuDesk Operations Studio                                |
|                 (Streamlit Front-End + High-Contrast Theme)                       |
+-----------------------------------------------------------------------------------+
           |                                                       |
           | 1. Raw Call Transcript / Lead Info                    | 3. Dispatch JSON
           v                                                       v
+------------------------------------+             +--------------------------------+
|       ai_engine.py                 |             |       crm_dispatcher.py        |
|  - Google Gemini (Flash-Lite / Flash)|             |  - HTTP POST with retry logic  |
|  - Pydantic Structured Outputs     |             |  - Simulation Mode Fallback    |
|  - Model-Agnostic Schema Guards    |             +--------------------------------+
+------------------------------------+                             |
           |                                                       | 4. Webhook Trigger
           v 2. Validated Schema Instances                         v
+-----------------------------------------------------------------------------------+
|                        Local Orchestrator: n8n (Docker)                           |
|       Endpoint: http://localhost:5678/webhook/nudesk-triage                       |
+-----------------------------------------------------------------------------------+
           |                                                       |
           | Branch A: Credit Operations                           | Branch B: Sales Operations
           v                                                       v
+------------------------------------+             +--------------------------------+
|  - Underwriting Google Sheet Row   |             |  - Sales Pipeline CRM Update   |
|  - Asana Task Creation via API     |             |  - Gmail Outbox Draft Staging  |
+------------------------------------+             +--------------------------------+
```

---

## 3. Repository Structure

```text
nudesk-ai-ops-pipeline/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI pipeline (Python 3.10 & 3.11)
├── .env.example                # Template for environment configuration
├── .gitignore                  # Exclusions (ignoring .env and SQLite DBs)
├── Makefile                    # Developer commands (install, test, run, tunnel)
├── README.md                   # Technical documentation and evaluation brief
├── requirements.txt            # Minimal, pinned Python dependencies
├── docker-compose.yml          # Container configuration for local n8n instance
├── n8n_workflow_blueprint.json # Importable workflow blueprint for n8n
├── app.py                      # V2 Enterprise nuDesk Operations Studio
├── app_v1_legacy.py            # V1 Prototype reference backup
├── auth_rbac.py                # Google Cloud Console OAuth 2.0 & RBAC engine
├── database.py                 # SQLite persistent audit trail & operations log
├── document_reader.py          # Multi-modal collateral ingestion (URLs & files)
├── meeting_queue.py            # Automated meeting queue (Read AI / Fireflies simulator)
├── models.py                   # Pydantic schemas (Credit, Sales, HR)
├── ai_engine.py                # Multi-model inference cascade (Gemini 3.5 Flash-Lite)
├── crm_dispatcher.py           # Resilient webhook dispatcher to n8n
├── mock_data.py                # Benchmark transcripts and candidate records
├── styles/
│   └── nudesk_theme.py         # Design system tokens and Light/Dark theme engine
├── scripts/
│   └── start_tunnel.sh         # One-click Cloudflare HTTPS tunnel for mobile demo
└── tests/
    └── test_v2_suite.py        # Automated test suite (Pydantic, RBAC, OAuth, DB)
```

---

## 4. Quickstart Installation Guide

### Prerequisites
- Python 3.10+ installed
- Docker & Docker Compose (optional, for local n8n testing)
- (Optional) Free Google AI Studio API key from [aistudio.google.com](https://aistudio.google.com/)
- (Optional) Google Cloud Console OAuth 2.0 Credentials for Live Google Login

### Step 1: Clone and Set Up Virtual Environment
```bash
git clone https://github.com/opyntorr/nudesk-ai-ops-pipeline.git
cd nudesk-ai-ops-pipeline

python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies via Makefile or pip
make install
```

### Step 2: Configure Environment
```bash
cp .env.example .env
```
- **Live AI Mode:** Open `.env` and paste your `GEMINI_API_KEY`.
- **Google OAuth 2.0:** Enter `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` from Google Cloud Console. Set Authorized redirect URIs to `http://localhost:8501`.
- **Demonstration Mode (Zero Config):** If left blank, the application launches in 100% transparent **Demonstration Mode**. Evaluators can test all dashboard metrics, inspect risk tiers, generate Asana tasks, view outreach drafts, and switch between simulated corporate roles.

### Step 3: Run the Dashboard
```bash
make run
# Or directly:
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 5. Developer Commands (Makefile)

Common workflows are automated through standard Makefile targets:

| Command | Description |
|---|---|
| `make install` | Installs all Python dependencies into the active environment |
| `make test` | Executes the full automated test suite with verbose reporting |
| `make run` | Starts the Streamlit dashboard on port 8501 |
| `make tunnel` | Launches the Cloudflare HTTPS tunnel for cross-device mobile testing |
| `make docker-up` | Launches the local n8n workflow container in the background |
| `make docker-down` | Gracefully shuts down the local n8n container |
| `make clean` | Removes bytecode caches and temporary files |

---

## 6. Continuous Integration (CI/CD)

Every push and Pull Request to this repository triggers an automated CI pipeline via **GitHub Actions** (`.github/workflows/ci.yml`):
- Verifies clean Python syntax compilation across all operational modules.
- Executes the full unit test suite on both **Python 3.10** and **Python 3.11**.
- Guarantees zero regression on Pydantic schemas, RBAC logic, OAuth URL generators, and database operations.

---

## 7. Running the Local n8n Orchestrator (Docker)

To test end-to-end webhook dispatch and Google Workspace routing locally:

1. Launch n8n:
   ```bash
   make docker-up
   ```
2. Access the visual editor at `http://localhost:5678/`.
3. Click **Workflows** -> **Import from File** and select `n8n_workflow_blueprint.json`.
4. Click **Activate Workflow**.
5. Click **Approve & Sync** inside the Streamlit dashboard to watch records flow into n8n in real time.

---

## 8. Mobile & Remote Demo Access (Cloudflare Tunnel)

To test or demo the dashboard on mobile devices (iOS / Android) or external computers without complex port-forwarding:

```bash
make tunnel
```
A public HTTPS link (e.g. `https://*.trycloudflare.com`) is generated to access the dashboard securely from any mobile or desktop browser.

---

## 9. Authors & Engineering Credits

- **Lead Operations & Automation Engineer:** Christian Omar Payán Torróntegui ([@opyntorr](https://github.com/opyntorr))
- **AI Architecture & Implementation Co-pilot:** Antigravity (Google DeepMind)
