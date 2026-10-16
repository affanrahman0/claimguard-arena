# ClaimGuard Arena

**An AI fraud defender for motor insurance claims, stress-tested by an AI attacker.**
Built by team **Argus Trace** for the Google Cloud AI Builder Cup 2026 (BFSI theme).

All data is synthetic. No real insurer, client or employer data is used anywhere.

## What it does

Insurance fraud rarely looks suspicious in one claim. It shows up when claims are connected: the same workshop, bank account, phone or photo. ClaimGuard Arena has three parts:

| Part | Folder | Job |
|---|---|---|
| **Defender** | `defender/` | Agents read a claim, check the policy, search claim history for hidden links, score the risk and recommend `fast_track`, `investigate` or `escalate`. A human adjuster always decides. |
| **Attacker** | `attacker/` | Generates clearly labelled synthetic fake claims (4 attack types, each with a harder "stealth" variant) to try to fool the defender. |
| **Evaluator** | `evaluator/` | The Arena. Runs attacks, honest claims and known fraud-ring claims through the defender and reports catch rate, false positives, misses and a suggested new check for each miss. |

The demo story: a ring claim looks clean alone, the link graph exposes 10 other claims, the attacker then fires fake claims, and the scoreboard shows what was caught, what slipped through and how to improve.

## Quick start (local, no API key needed)

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m shared.dataset                                # creates data/claims.db (synthetic)
python -m pytest -q tests                               # 10 tests should pass
uvicorn app.main:app --reload --port 8080               # open http://localhost:8080
python -m evaluator.runner --per-type 8 --legit 40      # Arena from the command line
```

Without credentials the app runs in **mock mode**: all the logic works, and the Gemini steps (consistency review, explanations, attack narratives, suggestions) use deterministic stand-ins. Header of the UI shows `LLM: mock` or `LLM: gemini`.

### Turning on Gemini
1. Get a key from Google AI Studio. Copy `.env.example` to `.env` and set `GEMINI_API_KEY=...`.
2. Check the current model IDs in AI Studio and set `MODEL_FAST` / `MODEL_REASON`.
3. Restart. The header should now say `LLM: gemini`. If a live call fails, the app falls back to mock for that step and reports `fallback` in the agent event.

## Project structure

```
claimguard-arena/
├── shared/            # contracts and plumbing both sides use
│   ├── schemas.py     # all Pydantic data contracts (the "API" between folders)
│   ├── domain.py      # insurance domain data: parts, clauses, thresholds
│   ├── dataset.py     # synthetic data generator (ring + decoy + hero claims)
│   ├── store.py       # SQLite data access (swap for BigQuery here)
│   ├── llm.py         # Gemini wrapper with mock fallback
│   └── config.py
├── defender/
│   ├── agents/        # intake.py, policy.py, fraud.py, decision.py
│   ├── tools/         # link_analysis.py, arithmetic.py
│   └── orchestrator.py
├── attacker/
│   ├── attacks.py     # the 4 attack generators
│   └── generator.py   # public entry points
├── evaluator/
│   ├── runner.py      # builds the test set, runs the Arena
│   ├── metrics.py     # scoreboard + suggested fixes
│   └── results/       # latest.json
├── app/
│   ├── main.py        # FastAPI routes
│   └── static/index.html   # UI: Defender / Attacker / Arena tabs
├── tests/  docs/  Dockerfile  requirements.txt  .env.example
```

**Rule for working in parallel:** the attacker and defender only talk through `shared/schemas.py`. Change a schema, tell your teammate.

## How scoring works (transparent on purpose)

`risk_score = min(100, sum of signal weights)`. Below 30 → fast track, 30 to 60 → investigate, above 60 → escalate.

| Signal | Weight | Source |
|---|---|---|
| Incident outside policy period | 40 | policy |
| Excluded damage type | 30 | policy |
| Narrative / photo / estimate mismatch | 30 | Gemini review |
| Itemised lines do not match claimed total | 30 | rules |
| Payout account in 2+ other claims | 25 (1 other: 5) | link analysis |
| Reused photo | 25 | link analysis |
| Same claimant, same damage type before | 20 | link analysis |
| Amount ≥ 1.8x typical for damage type | 20 | rules |
| Workshop cluster (interlinked claims) | 20 | link analysis |
| Shared phone | 15 (1 other: 3) | link analysis |
| Over coverage limit | 15 | policy |

The **decoy** workshop (W005, "CityFix Motors") has very high volume but no shared accounts, phones or photos, so it is correctly cleared. The **ring** (W017, "Apex Auto Works") has 11 interlinked claims.

## Deploy to Google Cloud Run

Run locally and make sure the tests pass first. Then (replace `PROJECT_ID`; also read the official hackathon deployment instructions):

```bash
gcloud auth login
gcloud config set project PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com aiplatform.googleapis.com

# Option A: Vertex AI (recommended on Cloud Run, no key stored)
gcloud run deploy claimguard-arena --source . --region asia-southeast1 --allow-unauthenticated \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1,MODEL_FAST=<model>,MODEL_REASON=<model>
# then give the service account the "Vertex AI User" role:
#   gcloud projects add-iam-policy-binding PROJECT_ID --member=serviceAccount:<RUN_SERVICE_ACCOUNT> --role=roles/aiplatform.user

# Option B: API key (store it in Secret Manager rather than plain env vars)
```
Before recording the demo: `--min-instances 1` to avoid cold starts, and set a billing budget alert. Check which locations support your chosen model.

## Known limits (be honest about these in the deck)
- Data and policy are synthetic; results show the approach works, not production accuracy.
- The prototype uses SQLite inside the container. BigQuery is the production path (re-implement `shared/store.py`).
- The attacker produces labelled synthetic test claims only. It does not detect or defeat real-world image forensics.
- The Gemini code paths are written against the `google-genai` SDK but need your first live run to confirm model names and output formats.

## Roadmap
See `docs/TASKS.md` for the split of work and day-by-day plan.
