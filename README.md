# DeskMate Operations Studio
### AI-Powered Credit Triage & Sales Acceleration Engine for Financial Services (FinServ)
**nuDesk MX Technical Assessment | Candidate: Christian Omar Payán Torróntegui**

---

## 1. Executive Summary & Business Context

At **nuDesk MX**, operational teams in Mazatlán, Sinaloa partner with US commercial lenders, regional banks, and factoring firms to streamline debt origination, sales outreach, and underwriting workflows. 

Traditional BPOs scale operational capacity by linearly increasing headcount ("seat count"), resulting in high overhead, employee fatigue on manual data entry, and delayed turnaround times. nuDesk disrupts this paradigm through the **Cyborg Organization Model**: pairing bilingual human specialists with domain-trained AI agents (**DeskMates**) to multiply productivity while safeguarding credit compliance.

**DeskMate Operations Studio** is an enterprise-ready prototype designed to eliminate the two most common operational bottlenecks faced by nuDesk teams:

1. **Credit Operations (Post-Call Discovery Triage):**
   - **The Problem:** Loan officers and discovery agents conduct 15-to-30 minute calls with US business owners. Manually listening to recordings or reading transcripts to extract financial parameters (debt, revenue, equipment quotes, tax liens) and creating underwriting tickets takes 40+ minutes per file.
   - **The Solution:** Ingests raw call transcripts (from dialers or Fireflies.ai), extracts key financial variables into strict Pydantic JSON schemas, computes an initial risk tier (Low, Moderate, High), isolates underwriting red flags, and automatically generates prioritized action items for the underwriting team (Asana-ready).

2. **Sales Operations (BDR Lead Scoring & Rapid Outreach):**
   - **The Problem:** Business Development Representatives (BDRs) in Mazatlán prospecting US logistics, construction, and manufacturing companies must manually research company viability, assess working capital fit, and draft custom outreach messages.
   - **The Solution:** Ingests raw commercial prospect profiles, computes a lead score from 1 to 100 based on urgency and collateral viability, provides clear underwriting rationale, and generates both an executive cold email draft and a 30-second telephone pitch tailored for high-conversion speed-to-lead dialing.

3. **Enterprise Dispatch & Hyperautomation (n8n & Google Workspace):**
   - Validated data structures are dispatched via HTTP POST webhooks to a local **n8n** orchestration engine (running in Docker), which routes and persists data into Google Sheets (acting as a live CRM/Pipeline tracker) and stages email drafts.

---

## 2. Architectural Highlights & "Harness Engineering"

A foundational principle of this project is **Model-Agnostic Architecture**. 

Large Language Models (LLMs) are evolving at rapid speed. Designing business software directly coupled to a specific model creates brittle systems vulnerable to API deprecation or vendor lock-in. 

In this application, the LLM is treated strictly as an interchangeable inference engine. The permanent enterprise value resides in the **Harness**:
- **Strict Data Contracts:** Pydantic schemas enforce type safety and structure at compile and runtime.
- **Fail-Safe Fallback:** If an API key is absent, expired, or rate-limited, the application gracefully transitions to Demonstration Mode, providing realistic synthetic records without throwing runtime exceptions.
- **Decoupled Orchestration:** Workflow routing, data transformation, and CRM synchronization are handled by n8n, ensuring that changes to downstream destinations (e.g. migrating from Google Sheets to HubSpot or Salesforce) require zero changes to the core AI engine.

```text
+-----------------------------------------------------------------------------------+
|                           nuDesk Operations Studio                                |
|                           (Streamlit Front-End)                                   |
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
├── .env.example                # Template for environment configuration
├── .gitignore                  # Exclusions (ignoring .env and SQLite DBs)
├── README.md                   # Technical documentation and evaluation brief
├── requirements.txt            # Minimal, pinned Python dependencies
├── docker-compose.yml          # Container configuration for local n8n instance
├── n8n_workflow_blueprint.json # Importable workflow blueprint for n8n
├── app.py                      # V2 Enterprise DeskMate Operations Studio
├── app_v1_legacy.py            # V1 Prototype reference backup
├── auth_rbac.py                # Google Workspace SSO & Role-Based Access Control
├── database.py                 # SQLite persistent audit trail & operations log
├── document_reader.py          # Multi-modal collateral ingestion (URLs & files)
├── meeting_queue.py            # Automated meeting queue (Read AI / Fireflies simulator)
├── models.py                   # Pydantic schemas (Credit, Sales, HR)
├── ai_engine.py                # Multi-model inference cascade (Gemini 3.5 Flash-Lite)
├── crm_dispatcher.py           # Resilient webhook dispatcher to n8n
├── mock_data.py                # Benchmark transcripts and candidate records
├── styles/
│   └── nudesk_theme.py         # Design system tokens directly from nudesk.ai
├── scripts/
│   └── start_tunnel.sh         # One-click Cloudflare HTTPS tunnel for mobile demo
└── tests/
    └── test_v2_suite.py        # Automated test suite for schemas, RBAC, and DB
```


---

## 4. Quickstart Installation Guide

### Prerequisites
- Python 3.10+ installed
- Docker & Docker Compose (optional, for local n8n testing)
- (Optional) Free Google AI Studio API key from [aistudio.google.com](https://aistudio.google.com/)

### Step 1: Clone and Set Up Virtual Environment
```bash
# Navigate to the project directory
cd /path/to/nudesk-operations-studio

# Create a virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment (Optional)
```bash
cp .env.example .env
```
- **Live AI Mode:** Open `.env` and paste your `GEMINI_API_KEY` (obtainable for free at [aistudio.google.com](https://aistudio.google.com/)). You can also enter the key directly in the Streamlit web sidebar.
- **Demonstration Mode (Zero Config):** If left blank, the application launches in 100% transparent **Demonstration Mode**. Evaluators can test all dashboard metrics, inspect risk tiers, generate Asana operational tasks, view sales outreach drafts, and trigger n8n webhooks immediately without needing their own Google Cloud or AI Studio credentials.

### Step 3: Run the Streamlit Dashboard
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 5. Running the Local n8n Orchestrator (Docker)

To test end-to-end webhook dispatch and Google Workspace routing locally:

### 1. Launch n8n in Docker
```bash
docker compose up -d
```

### 2. Access n8n Visual Editor
Open `http://localhost:5678/` in your browser. Complete the quick initial admin account setup.

### 3. Import Workflow Blueprint
1. In the n8n interface, click **Workflows** -> **Import from File**.
2. Select the `n8n_workflow_blueprint.json` file included in this repository.
3. Click **Activate Workflow**.
4. Test clicking the **Dispatch** buttons inside the Streamlit dashboard to watch records flow into the n8n execution log in real time.

---

## 6. Demonstration Data Profiles (FinServ US)

The application includes two preloaded, realistic test cases:

- **Credit Operations Demo:** A post-call discovery transcript featuring *Robert Martinez*, owner of *Apex Fleet Repair* (Dallas, TX). The borrower seeks an $85,000 USD equipment term loan for hydraulic lifts against $38,000 USD monthly gross revenue, while disclosing an active IRS tax lien under an approved installment agreement. The system categorizes the file as *Moderate Risk*, isolates the lien, and assigns verification tasks to Credit Analysts and Compliance Officers.
- **Sales Operations Demo:** A commercial profile for *Sunbelt Logistics LLC* (Phoenix, AZ), a 14-tractor refrigerated fleet with $2.4M USD annual revenue facing 60-day freight broker payment terms. The system scores the lead at *88/100* for Invoice Factoring and generates an executive cold email and telephone script ready for immediate BDR execution.

---

## 7. Compliance, Testing & Technical Rigor

- **Type Safety:** All inputs and outputs are governed by Pydantic models.
- **Automated Test Suite:** Run `python -m unittest tests/test_v2_suite.py` to verify schema serialization, RBAC permissions, meeting queues, and SQLite database persistence.
- **No Unhandled Crashes:** All network calls, API timeouts, and missing credentials are caught with user-friendly warnings rather than raw tracebacks.
- **SOC 2 & Privacy Awareness:** Local execution on Docker and model-agnostic payload formatting ensure financial client data can be retained in private infrastructure.

---

## 8. Mobile & Remote Demo Access (Cloudflare Tunnel)

To test or demo the dashboard on mobile devices (iOS / Android) or external computers without complex port-forwarding:

```bash
# Run the automated tunnel script
./scripts/start_tunnel.sh
```
A public HTTPS link (e.g. `https://*.trycloudflare.com`) will be generated to access the dashboard securely from any browser.

---

## 9. Authors & Engineering Credits


- **Lead Operations & Automation Engineer:** Christian Omar Payán Torróntegui ([@opyntorr](https://github.com/opyntorr))
- **AI Architecture & Implementation Co-pilot:** Antigravity (Google DeepMind)

