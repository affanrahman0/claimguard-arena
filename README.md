# 🛡️ ClaimGuard Arena (Argus Trace)
### *Next-Gen Multi-Agent BFSI Insurance Fraud Defense & Adversarial Red-Team Arena*

[![Google Cloud](https://img.shields.io/badge/Google_Cloud-Vertex_AI_%7C_Cloud_Run-4285F4?logo=googlecloud&logoColor=white)](https://cloud.google.com/)
[![Gemini 3.8 Flash](https://img.shields.io/badge/Model-Gemini_3.8_Flash-8E75B2?logo=googlegemini&logoColor=white)](https://ai.google.dev/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Hackathon](https://img.shields.io/badge/Hackathon-Google_Cloud_AI_Builder_Cup_2026-FFA116)](https://cloud.google.com)

---

## 📌 Executive Summary

Motor insurance fraud drains **$30+ Billion annually** in the US alone, with **8% to 10%** of all claims involving some form of exaggeration or organized staging. 

Traditional rule engines fail because sophisticated syndicates engineer individual claims to appear completely normal in isolation. Fraud only surfaces when claims are viewed across a **multi-dimensional link network**—connected by shared bank accounts, burner phones, collusive repair workshops, and recycled accident photos.

**ClaimGuard Arena (built by Team Argus Trace)** introduces a resilient, dual-sided architecture:
1. **Multi-Agent Defense Pipeline:** 4 orchestrated AI agents (*Intake*, *Policy*, *Fraud*, and *Decision*) adjudicate claims with transparent, mathematically explainable risk scoring (0–100).
2. **AI SIU Interrogation Copilot:** Powered by Google Gemini, the copilot cross-examines claimant statements in real time, generates targeted interrogation questions, detects psychological deception markers, and scores statement plausibility (0–100).
3. **Forensic Audit Dossier:** Generates courtroom-ready, regulatory-compliant (NAIC-standard) audit packets with MD5 photo chain-of-custody, contractual clause matrices, syndicate link visualizations, and sworn sign-off blocks.
4. **Adversarial Red-Team Attacker & Arena Benchmark:** An embedded adversary continuously generates synthetic attack claims across 4 vectors (with stealth variants) to probe defense perimeter blind spots and suggest concrete rule improvements.

> **Note on Data Ethics:** All policies, claims, vehicles, garages, and claimant identities used in this project are 100% synthetically generated. No real policyholder or insurer PII is ever ingested or stored.

---

## 🏛️ System Architecture

```
                                 ┌────────────────────────────────────────────────────────┐
                                 │                   UNSTRUCTURED INPUTS                  │
                                 │  (Police FIRs, Towing Bills, Driver Emails, Invoices)  │
                                 └───────────────────────────┬────────────────────────────┘
                                                             │
                                                             ▼
                                                [ Tab 4: Document AI Intake ]
                                                 (Gemini Structured Extraction)
                                                             │
                                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                             CLAIMGUARD MULTI-AGENT DEFENDER                                            │
│                                                                                                                        │
│   ┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐     ┌───────────────────────────────┐   │
│   │   1. INTAKE AGENT  │ ──► │  2. POLICY AGENT   │ ──► │   3. FRAUD AGENT   │ ──► │       4. DECISION AGENT       │   │
│   │  Schema validation │     │ Contractual limits │     │ Repair cost audit  │     │  0–100 Mathematical Formula   │   │
│   │  Date sequencing   │     │ Active date bounds │     │ Syndicate link net │     │  • Fast-Track (STP)  (<30)    │   │
│   │  Photo hash checks │     │ Exclusion clauses  │     │ Narrative mismatch │     │  • Investigate       (30-60)  │   │
│   └────────────────────┘     └────────────────────┘     └────────────────────┘     │  • Escalate to SIU   (>60)    │   │
│                                                                                    └───────────────┬───────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────────────────┼───────────────────┘
                                                                                                     │
                                                ┌────────────────────────────────────────────────────┴──────────────┐
                                                ▼                                                                   ▼
                             ┌─────────────────────────────────────┐                             ┌─────────────────────────────────────┐
                             │        AI SIU COPILOT (GEMINI)      │                             │       COURTROOM FORENSIC DOSSIER    │
                             │ • Claimant Cross-Examination        │                             │ • One-Click Regulatory PDF Export   │
                             │ • Live 0–100 Plausibility Index     │                             │ • MD5 Chain of Custody & Blueprints │
                             │ • Deception Markers & Target Qs     │                             │ • Contract Clause Audit Checklist   │
                             │ • Human Investigator Audit Trail    │                             │ • Sworn Adjuster Sign-Off Block     │
                             └─────────────────────────────────────┘                             └─────────────────────────────────────┘
                                                ▲
                                                │ (Stress Tests Defenses)
┌───────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────┐
│                                         ADVERSARIAL RED-TEAM ARENA & EVALUATOR                                         │
│                                                                                                                        │
│   ┌────────────────────────────────────────┐                       ┌───────────────────────────────────────────────┐   │
│   │            RED-TEAM ATTACKER           │                       │               ARENA BENCHMARK                 │   │
│   │  Synthesizes 4 adversarial vectors:    │ ────────────────────► │  Batch tournament testing:                    │   │
│   │  1. Inconsistent Narrative vs Photo    │                       │  • Catch Rate (%)     • False Positive Rate   │   │
│   │  2. Excluded Peril Camouflage          │                       │  • Syndicate Recall   • Perimeter Gap Fixes   │   │
│   │  3. Inflated Repair Billing            │                       │                                               │   │
│   │  4. Distributed Collusion Ring         │                       │  Interactive Miss Inspection & Clause Drawers │   │
│   └────────────────────────────────────────┘                       └───────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Key Capabilities

### 1. 📋 Document AI Intake
* **Unstructured Ingestion:** Ingests raw police accident reports (FIRs), repair shop invoices, towing slips, and claimant statement emails.
* **Schema Normalization:** Leverages Google Gemini structured JSON extraction to map free text into validated Pydantic models (`policy_id`, `incident_date`, `damage_type`, `line_items`, `workshop_id`, `bank_account`, `phone`).
* **Direct Pipeline Bridge:** Allows adjusters to extract any document and instantly route it through the 4-agent defense engine with one click.

### 2. 🛡️ Multi-Agent Defense Engine
* **Intake Agent:** Performs sanity checks on date chronologies (incident vs. filing) and validates itemized part specifications.
* **Policy Agent:** Executes strict clause verification against policy contracts (Clause 3.1–3.3 for covered perils, Clause 4.1–4.2 for wear-and-tear/mechanical exclusions, Clause 5.1 for policy period validity, Clause 5.2 for coverage limits).
* **Fraud Agent:** Audits repair bills against domain medians, runs cross-claim link analysis, and evaluates narrative-damage consistency.
* **Decision Agent:** Synthesizes all agent outputs into a transparent, additive score with clear action recommendations (`fast_track`, `investigate`, `escalate`).
* **Progressive Pipeline Stepping:** Live visual feedback displaying agent-by-agent execution, step latencies (ms), and signal attribution tags.

### 3. 🕸️ Cross-Claim Syndicate Link Graph
* **Collusion Ring Discovery:** Traverses the claim database to uncover shared entities that are invisible on single-claim reviews (shared bank accounts, telephone numbers, shady repair workshops, and duplicate photo hashes).
* **Decoy vs. Ring Differentiation:** Correctly differentiates between legitimate high-volume repair shops (e.g., Decoy Workshop `W005 "CityFix Motors"`) and organized fraud rings (e.g., Ring Workshop `W017 "Apex Auto Works"` with 11 interlinked claims).

### 4. 🧠 AI SIU Interrogation Copilot *(Powered by Gemini)*
* **Cross-Examination Generator:** Analyzes claimant narratives, damage locations, and invoices to synthesize 3 targeted, high-leverage interrogation questions for SIU investigators.
* **Live Plausibility Gauge:** Dynamically evaluates claimant explanations on a 0–100 plausibility scale.
* **Deception Cues:** Flags psychological deception markers (e.g., excessive timeline vagueness, deflection, unprompted alibis, physics inconsistencies).
* **Adjuster Audit Trail:** Persists all SIU copilot evaluations and adjuster actions directly into the audit log.

### 5. ⚖️ Courtroom-Ready Forensic Dossier
* **Regulatory Compliance:** Formats evidence according to statutory fraud reporting standards (NAIC Model Legislation compliant).
* **Forensic Verification:** Contains vehicle damage blueprints, itemized invoice variance tables, cryptographic MD5 photo hash validation, and syndicate network summaries.
* **Courtroom Utility:** Includes complete policy contract clause checklists, investigator notes, and a sworn sign-off block exportable to clean PDF via `@media print`.

### 6. ⚔️ Red-Team Adversarial Attacker & Arena Benchmark
* **4 Synthetic Attack Vectors:**
  1. *Inconsistent Narrative:* Fabricated accident descriptions conflicting with vehicle damage photos.
  2. *Excluded Peril Camouflage:* Masking wear-and-tear or track racing as covered road collisions.
  3. *Inflated Invoicing:* Phantom parts and 200%+ markup over regional benchmarks.
  4. *Syndicate Injection:* Claims sharing bank accounts and burner phones with known rings.
* **Stealth Variants:** Subtly tunes amounts and wording just beneath typical static rule thresholds.
* **Continuous Tournament Benchmarking:** Runs automated tournaments over test batches to score catch rate, false-positive rate, and ring recall.
* **Perimeter Improvement Suggestions:** For every missed adversarial claim, the Arena uses Gemini to suggest concrete, actionable rule improvements.

---

## 🔢 Explainable Scoring Model

ClaimGuard Arena explicitly rejects opaque "black-box" decisions. Every claim is assigned a mathematical score from **0 to 100** derived from additive statutory risk weights:

$$\text{Final Risk Score} = \min\left(100, \sum \text{Signal Weights}\right)$$

| Signal Detected | Weight | Detection Source | Statutory Rationale |
| :--- | :---: | :--- | :--- |
| **Incident Outside Policy Period** | `+40` | Policy Agent (Clause 5.1) | No active insurance contract exists |
| **Excluded Damage Type** | `+30` | Policy Agent (Clause 4.1/4.2) | Wear & tear or mechanical breakdown |
| **Narrative / Photo Mismatch** | `+30` | Gemini Consistency Review | Claimant statement contradicts physical evidence |
| **Itemized Lines ≠ Claim Total** | `+30` | Intake Arithmetic Audit | Invoiced parts do not sum to claimed amount |
| **Bank Account in 2+ Other Claims** | `+25` | Graph Link Analysis | Payout diversion / shared financial node (`+5` if 1 other) |
| **Reused Photo Hash** | `+25` | Digital Forensic Audit | Recycled damage photo from historical claim |
| **Claimant History (Same Damage)** | `+20` | Graph Link Analysis | Prior identical claim filed by same individual |
| **Amount ≥ 1.8x Domain Median** | `+20` | Fraud Arithmetic Audit | Excessive billing beyond regional benchmark |
| **Workshop Cluster (Collusion)** | `+20` | Graph Link Analysis | Repair facility linked to multiple anomalous claims |
| **Shared Phone Number** | `+15` | Graph Link Analysis | Burner phone linked across separate policies (`+3` if 1 other) |
| **Over Coverage Limit** | `+15` | Policy Agent (Clause 5.2) | Claim exceeds statutory policy schedule limit |

### Statutory Routing Thresholds
* **Score 0 – 29 (`fast_track`):** Low risk. Fast-tracked for instant Straight-Through Processing (STP) payout.
* **Score 30 – 60 (`investigate`):** Moderate risk. Routed to standard desk adjuster for document verification.
* **Score 61 – 100 (`escalate`):** High risk. Automatically routed to Special Investigation Unit (SIU) with full Dossier and Copilot active.

---

## 🛠️ Technology Stack

| Layer | Technologies | Purpose |
| :--- | :--- | :--- |
| **AI / Foundation Models** | **Google Gemini 3.8 Flash**, Gemini 3.5 Flash | Consistency analysis, SIU interrogation, document extraction, perimeter suggestions |
| **Cloud Platform** | **Google Cloud Run**, **Vertex AI** | Serverless container hosting, IAM authentication, Vertex Model Garden |
| **Backend Framework** | **Python 3.11+**, **FastAPI**, **Uvicorn** | High-performance asynchronous API service |
| **Data Contracts** | **Pydantic v2** | Strict schema validation between agents, attackers, and evaluators |
| **Storage & Graph** | **SQLite3** *(swap-ready for Google BigQuery)* | Relational claims database and indexed graph link traversal |
| **Frontend UI** | **Vanilla HTML5 / Modern CSS / ES6 JavaScript** | Obsidian cyber-command design, Vis.js link graphs, responsive drawer accordions, `@media print` |
| **Testing & CI** | **pytest**, **HTTPX** | Comprehensive test coverage (10/10 automated test suites) |

---

## 🚀 Quick Start Guide

ClaimGuard Arena features **zero-friction local execution**. It includes an intelligent **deterministic mock fallback engine**, allowing judges and developers to run the entire application, pass all tests, and explore the complete UI **without needing an API key or Google Cloud account**.

### 1. Clone & Set Up Virtual Environment

```bash
# Clone the repository
git clone https://github.com/affanrahman0/claimguard-arena.git
cd claimguard-arena

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt
```

### 2. Initialize Synthetic Dataset

```bash
# Generates data/claims.db with synthetic policies, rings, decoys, and hero claims
python -m shared.dataset
```

### 3. Run Automated Test Suite

```bash
# Execute all 10 unit and pipeline test suites
python -m pytest -v tests
```
*(All 10 tests should pass in under 0.5s).*

### 4. Start the Application

```bash
# Launch FastAPI development server
uvicorn app.main:app --reload --port 8080
```
Open your browser to: **`http://localhost:8080`**

---

## 🔑 Activating Google Gemini & Vertex AI

When running without credentials, the UI badge indicates `LLM: mock` and uses deterministic simulation. To enable live Google Gemini models:

### Option A: Google AI Studio API Key (Local Development)
1. Get a free API key from [Google AI Studio](https://aistudio.google.com/).
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and set your key:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   MODEL_FAST=gemini-3.8-flash
   MODEL_REASON=gemini-3.8-flash
   ```
4. Restart Uvicorn. The UI header will now display: `LLM: gemini`.
   *(Note: The system features an automatic failover pool: `gemini-3.8-flash` ➔ `gemini-3.5-flash` ➔ mock fallback to ensure zero downtime).*

### Option B: Google Cloud Vertex AI (Enterprise / Cloud Run)
Set environment variables to route directly through Google Cloud Vertex AI using Service Account IAM:
```bash
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
export MODEL_FAST="gemini-3.8-flash"
export MODEL_REASON="gemini-3.8-flash"
```

---

## ☁️ Deploying to Google Cloud Run

ClaimGuard Arena is packaged for containerized deployment to Google Cloud Run:

```bash
# 1. Authenticate with Google Cloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Enable necessary Google Cloud APIs
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com

# 3. Deploy to Cloud Run using Vertex AI
gcloud run deploy claimguard-arena \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 1 \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1,MODEL_FAST=gemini-3.8-flash,MODEL_REASON=gemini-3.8-flash

# 4. Grant Vertex AI User role to the Cloud Run service account
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

---

## 🖥️ Interactive User Walkthrough

When you open `http://localhost:8080`, you will experience 4 integrated modules:

### 1. 🛡️ Tab 1: Multi-Agent Defender
* **Claim Inspector:** Select any sample claim (e.g. `CLM-0001` to `CLM-0010` or Hero Ring Claim `CLM-0081`).
* **Progressive Pipeline Stepping:** Click **"⚡ Analyze Claim"** to observe real-time pipeline execution as Intake, Policy, Fraud, and Decision agents run sequentially with animated latency meters and signal tags.
* **Transparent Formula Card:** Inspect the exact mathematical score calculation ($\text{Base } 0 + \text{Policy } +X + \text{Fraud } +Y = Z/100$) with statutory threshold indicators.
* **SIU Interrogation Copilot:** Click **"🧠 Launch SIU Copilot"** on flagged claims to interactively cross-examine claimant statements, generate questions, and gauge plausibility.
* **Courtroom Forensic Dossier:** Click **"⚖️ Courtroom Dossier"** to open a NAIC-compliant audit record with MD5 photo verification and printable PDF formatting.

### 2. 🕸️ Tab 2: Syndicate Link Graph
* **Interactive Network:** Powered by Vis.js physics simulation. Select any claim to visualize 1st- and 2nd-degree connections.
* **Entity Pinpointing:** See how claims share bank accounts (`SYN-ACC-...`), phone numbers (`SYN-PH-...`), and duplicate photos (`PH-RING-...`).
* **Hero Demonstration:** Inspect `CLM-0081` connected to the 11-claim ring at Workshop `W017 (Apex Auto Works)`. Compare against high-volume legitimate Decoy Workshop `W005 (CityFix Motors)`.

### 3. ⚔️ Tab 3: Attacker Lab & Arena Benchmark
* **Attacker Lab:** Inject individual adversarial claims across 4 vectors. Inspect the full Injected Adversarial Claim Specifications and Target Policy Terms using collapsible drawers.
* **Arena Tournament:** Run a tournament across synthetic attacks, honest claims, and ring claims.
* **Deep Inspection Drawers:** Click `[📋 Claim Specs]` and `[🛡️ Policy Terms]` on missed attacks to see exactly why an adversarial claim penetrated the perimeter.
* **Rule Tuning Engine:** Review AI-generated suggestions for hardening thresholds based on attack misses.

### 4. ✍️ Tab 4: File & Extract Claim (Document AI)
* **Unstructured Text Extraction:** Paste any raw police accident report, towing slip, or email.
* **Entity Parsing:** Click **"Extract Structured Entities"** to convert natural language into a validated JSON schema.
* **Live Adjudication:** Click **"Analyze Extracted Claim Through Defense Engine"** to push your extracted document through all 4 defense agents.

---

## 📁 Repository Structure

```
claimguard-arena/
├── shared/                     # Shared foundation contracts and plumbing
│   ├── schemas.py              # Pydantic v2 data models (contracts between all layers)
│   ├── domain.py               # Insurance domain rules (parts, clauses, price medians)
│   ├── dataset.py              # Synthetic claims, policies, and collusion ring generator
│   ├── store.py                # SQLite repository (indexed queries, link analysis graph)
│   ├── llm.py                  # Gemini SDK wrapper with failover pool & mock fallback
│   └── config.py               # Centralized configuration & environment loader
├── defender/                   # Multi-agent defense system
│   ├── agents/
│   │   ├── intake.py           # Intake agent (schema, chronologies, photo hash)
│   │   ├── policy.py           # Policy agent (contract clauses 3.1–5.2)
│   │   ├── fraud.py            # Fraud agent (line-item pricing, link graph, LLM review)
│   │   └── decision.py         # Decision agent (additive scoring, fast-track / escalate)
│   ├── tools/
│   │   ├── link_analysis.py    # Multi-hop graph link traversal
│   │   └── arithmetic.py       # Cost audit vs. regional benchmark medians
│   ├── copilot.py              # AI SIU Copilot (cross-examination, plausibility gauge)
│   └── orchestrator.py         # 4-agent execution pipeline & state coordinator
├── attacker/                   # Adversarial red-team generation engine
│   ├── attacks.py              # 4 adversarial attack vector implementations
│   └── generator.py            # Batch generation & stealth noise injectors
├── evaluator/                  # Arena tournament benchmarking
│   ├── runner.py               # Tournament runner & thread pool executor
│   ├── metrics.py              # Scoring metrics (catch rate, false-positives, recall)
│   └── results/                # Persisted tournament benchmark runs
├── app/                        # Web application & API layer
│   ├── main.py                 # FastAPI endpoints & REST routes
│   └── static/
│       └── index.html          # Enterprise UI (Command Center, Copilot, Dossier, Graph)
├── tests/                      # Automated test suite
│   ├── test_pipeline.py        # 10 comprehensive unit & end-to-end tests
│   └── test_gemini_live.py     # Optional live Gemini integration tests
├── Dockerfile                  # Production container configuration for Cloud Run
├── requirements.txt            # Production runtime dependencies
├── requirements-dev.txt        # Development & test dependencies
└── README.md                   # Project documentation
```

---

## 🔮 Future Roadmap

As presented in our hackathon technical roadmap, planned post-hackathon platform evolutions include:

1. **Multimodal Vision Intake:** Direct ingestion of high-resolution vehicle damage photos into Gemini Vision for automated dent, panel, and paint damage classification.
2. **Perceptual Image Similarity (pHash):** Upgrading exact hash matching to perceptual and cosine embedding similarity to catch retaken photos of the same damage from altered angles.
3. **Line-Item OEM Price Curves:** Transitioning from broad repair category medians to part-specific OEM and aftermarket catalog price curves.
4. **Google BigQuery Data Warehouse:** Migrating the SQLite operational database to Google Cloud BigQuery for petabyte-scale historical fraud graph analytics.
5. **Vertex AI Search (Agentic RAG):** Implementing semantic RAG search across complex, multi-page commercial policy binders and endorsement riders.
6. **Google Agent Development Kit (ADK):** Wrapping our agent orchestrator in Google's official ADK framework for standardized multi-agent state management.

---

## 👥 Team Argus Trace

* **Project:** ClaimGuard Arena
* **Competition:** Google Cloud AI Builder Cup 2026
* **Category:** BFSI (Banking, Financial Services & Insurance)
* **Status:** Fully functional prototype with 10/10 automated tests passing, live Gemini integration, and Cloud Run deployment configuration.
