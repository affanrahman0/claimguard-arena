"""FastAPI app: ties defender, attacker and evaluator together and serves the UI.
Run locally:  uvicorn app.main:app --reload --port 8080"""
import random
import threading
from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from shared import config, dataset, domain, llm
from shared.schemas import CaseResult, Claim, LineItem
from shared.store import SqliteRepo
from attacker.generator import ATTACK_TYPES, generate_attack
from defender import copilot
from defender.agents import intake
from defender.orchestrator import analyze
from evaluator import runner

repo = SqliteRepo()
STATIC = Path(__file__).parent / "static"
ARENA = {"status": "idle", "done": 0, "total": 0, "error": None}
_arena_lock = threading.Lock()

HERO_META = {
    "CLM-HERO-CLEAN": {
        "title": "Clean Claim (Instant Fast-Track)",
        "tag": "Legitimate",
        "category": "clean",
        "badge": "Safe",
        "summary": "Genuine collision claim with valid policy, reasonable repair estimate, and zero suspicious history links."
    },
    "CLM-HERO-DECOY": {
        "title": "High-Volume Honest Workshop (Decoy)",
        "tag": "Decoy / Clean",
        "category": "decoy",
        "badge": "Volume != Fraud",
        "summary": "Filed at CityFix Motors (W005). Proves high claim volume does not trigger false positives without entity collusion."
    },
    "CLM-HERO-LAPSED": {
        "title": "Expired Policy (Out of Period)",
        "tag": "Policy Violation",
        "category": "policy",
        "badge": "Clause 5.1",
        "summary": "Incident occurred 25 days before policy start date. Caught by Policy Agent date verification."
    },
    "CLM-HERO-EXCLUDED": {
        "title": "Wear & Tear Damage (Excluded)",
        "tag": "Policy Exclusion",
        "category": "policy",
        "badge": "Clause 4.1",
        "summary": "Claim for routine brake pad & tyre replacement. Excluded by policy contract terms."
    },
    "CLM-RING-001": {
        "title": "Fraud Syndicate Member (Looks Clean Alone)",
        "tag": "Syndicate Ring",
        "category": "ring",
        "badge": "Apex Auto Ring",
        "summary": "Looks normal in isolation, but link graph reveals 10 other claims connected by shared bank accounts and garage."
    },
    "CLM-RING-005": {
        "title": "Fraud Ring Member (Recycled Photo)",
        "tag": "Syndicate + Image Hash",
        "category": "ring",
        "badge": "Reused Photo",
        "summary": "Apex Auto Works claim with an identical perceptual damage photo hash recycled from an earlier claim."
    },
    "CLM-RING-006": {
        "title": "Fraud Ring Member (Shared Phone/Bank)",
        "tag": "Syndicate + Identity",
        "category": "ring",
        "badge": "Shared Entity",
        "summary": "Shares payout account and claimant phone number with multiple active ring members."
    },
}


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not repo.exists():
        dataset.build()
    yield


app = FastAPI(title="ClaimGuard Arena", version="0.1.0", lifespan=lifespan)


class AnalyzeRequest(BaseModel):
    claim_id: Optional[str] = None
    claim: Optional[Claim] = None


class DecisionRequest(BaseModel):
    action: str  # approve | override | escalate
    note: str = ""


class LaunchRequest(BaseModel):
    attack_type: str = "clone_and_tweak"
    stealth: bool = False


class ArenaRequest(BaseModel):
    per_type: int = 8
    n_legit: int = 40


class ExtractRequest(BaseModel):
    text: str


class CopilotEvaluateRequest(BaseModel):
    question: str
    claimant_answer: str


def _store(case) -> dict:
    payload = case.model_dump(mode="json")
    repo.save_case(case.case_id, case.claim.claim_id, case.model_dump_json())
    repo.add_audit(case.case_id, "system", "analyzed", {"score": case.decision.risk_score, "recommendation": case.decision.recommendation})
    return payload


@app.get("/api/health")
def health():
    return {"status": "ok", "llm_mode": llm.mode(), "models": {"fast": config.MODEL_FAST, "reason": config.MODEL_REASON},
            "db_ready": repo.exists()}


@app.get("/api/claims/samples")
def samples():
    res = []
    for s in repo.list_samples():
        cid = s["claim_id"]
        meta = HERO_META.get(cid, {
            "title": cid, "tag": "Sample", "category": "general", "badge": "Demo", "summary": f"Claim {cid}"
        })
        res.append({**s, **meta})
    return res


@app.get("/api/claims")
def list_claims(limit: int = 30, offset: int = 0, q: Optional[str] = None):
    return repo.list_claims(limit=limit, offset=offset, query=q)


@app.get("/api/claims/{claim_id}")
def get_claim_detail(claim_id: str):
    claim = repo.get_claim(claim_id)
    if not claim:
        raise HTTPException(404, "Claim not found")
    return claim.model_dump(mode="json")


@app.get("/api/attacks/types")
def attack_types():
    return ATTACK_TYPES


@app.get("/api/workshops")
def get_workshops():
    return repo.list_workshops()


import base64
import uuid

class PhotoUploadRequest(BaseModel):
    image_data: str  # base64 data URL
    filename: Optional[str] = "damage_photo.jpg"


@app.post("/api/claims/upload-photo")
def upload_photo(req: PhotoUploadRequest):
    import hashlib
    raw = req.image_data
    if "," in raw:
        header, b64_str = raw.split(",", 1)
    else:
        b64_str = raw
    
    try:
        data = base64.b64decode(b64_str)
    except Exception as exc:
        raise HTTPException(400, f"Invalid base64 image data: {exc}")
    
    photo_hash = hashlib.md5(data).hexdigest()[:16]
    unique_name = f"upload_{photo_hash}_{uuid.uuid4().hex[:6]}.jpg"
    upload_dir = STATIC / "images" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    out_file = upload_dir / unique_name
    out_file.write_bytes(data)
    
    url = f"/static/images/uploads/{unique_name}"
    return {
        "photo_url": url,
        "photo_hash": photo_hash,
        "filename": req.filename or unique_name,
        "size_bytes": len(data)
    }


@app.get("/api/policies/{policy_id}")
def get_policy_detail(policy_id: str):
    pol = repo.get_policy(policy_id)
    if not pol:
        pol = {
            "policy_id": policy_id,
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "coverage_limit": 20000.0
        }
    return {
        "policy_id": pol["policy_id"],
        "start_date": pol["start_date"],
        "end_date": pol["end_date"],
        "coverage_limit": pol["coverage_limit"],
        "standard_deductible": 500.0,
        "product_tier": "Comprehensive Motor Vehicle Shield (Gold Tier)",
        "underwriter": "ClaimGuard Mutual Underwriting Corp",
        "holder_status": "Insured - Primary Vehicle Coverage",
        "insured_perils": [
            {"code": "Clause 3.1.A", "name": "Accidental Collision Damage", "limit": f"${pol['coverage_limit']:,.0f}"},
            {"code": "Clause 3.1.B", "name": "Windscreen & Auto Glass Replacement", "limit": "Full (Zero Deductible)"},
            {"code": "Clause 3.1.C", "name": "Animal Impact & Road Hazards", "limit": f"${pol['coverage_limit']:,.0f}"},
            {"code": "Clause 3.1.D", "name": "Theft, Vandalism & Malicious Damage", "limit": f"${pol['coverage_limit']:,.0f}"}
        ],
        "statutory_exclusions": [
            {"code": "Clause 4.1.A", "name": "Wear & Tear / Gradual Degradation", "status": "STRICTLY EXCLUDED"},
            {"code": "Clause 4.1.B", "name": "Mechanical / Electrical Breakdown", "status": "STRICTLY EXCLUDED"},
            {"code": "Clause 4.1.C", "name": "Pre-existing Unrepaired Structural Flaws", "status": "STRICTLY EXCLUDED"}
        ],
        "general_conditions": [
            {"clause": "Clause 5.1", "title": "Loss Period Verification", "rule": f"Loss event must occur on or after {pol['start_date']} and on or before {pol['end_date']}."},
            {"clause": "Clause 5.2", "title": "Maximum Loss Indemnity Cap", "rule": f"Aggregate claim payouts cannot exceed ${pol['coverage_limit']:,.0f}."}
        ]
    }


@app.get("/api/claims/{claim_id}/policy")
def get_claim_policy(claim_id: str):
    claim = repo.get_claim(claim_id)
    if not claim:
        raise HTTPException(404, "Claim not found")
    return get_policy_detail(claim.policy_id)


class CreateClaimRequest(BaseModel):
    claim_id: Optional[str] = None
    policy_id: Optional[str] = "POL-CUSTOM"
    claimant_id: Optional[str] = "CUS-USER-01"
    workshop_id: str = "W010"
    damage_type: str = "collision"
    amount_claimed: float = 2450.0
    incident_date: Optional[str] = "2026-06-15"
    filed_date: Optional[str] = "2026-06-16"
    narrative: str = "Vehicle sustained damage in traffic."
    bank_account: Optional[str] = "SYN-ACC-USER01"
    phone: Optional[str] = "SYN-PH-USER01"
    photo_caption: Optional[str] = ""
    photo_url: Optional[str] = None
    photo_hash: Optional[str] = None
    line_items: Optional[list[LineItem]] = None
    policy_active: bool = True


@app.post("/api/claims/create")
def create_custom_claim(req: CreateClaimRequest):
    import hashlib
    rnd = random.Random()
    cid = req.claim_id or f"CLM-USER-{rnd.randint(1000, 9999)}"
    pol_id = req.policy_id or f"POL-{cid}"
    inc_date = date.fromisoformat(req.incident_date) if req.incident_date else date(2026, 6, 15)
    fld_date = date.fromisoformat(req.filed_date) if req.filed_date else inc_date + timedelta(days=1)

    clean_damage_type = domain.normalize_damage_type(req.damage_type)
    if req.line_items:
        items = req.line_items
    else:
        raw_items = domain.make_items(clean_damage_type, req.amount_claimed, rnd)
        items = [LineItem(**it) for it in raw_items]

    caption = req.photo_caption or domain.make_caption(clean_damage_type, "front" if clean_damage_type == "collision" else None)
    photo_hash = req.photo_hash or hashlib.md5(f"{cid}-photo".encode()).hexdigest()[:16]

    # Resolve photo url
    if req.photo_url:
        p_url = req.photo_url
    elif clean_damage_type == "glass":
        p_url = "/static/images/glass_crack.jpg"
    elif clean_damage_type == "wear_and_tear":
        p_url = "/static/images/wear_and_tear.jpg"
    elif clean_damage_type in ("vandalism", "theft"):
        p_url = "/static/images/vandalism_scratch.jpg"
    elif "side" in req.narrative.lower():
        p_url = "/static/images/side_collision.jpg"
    elif "rear" in req.narrative.lower():
        p_url = "/static/images/rear_collision.jpg"
    elif req.workshop_id == "W017" or (req.bank_account and "R00" in req.bank_account):
        p_url = "/static/images/ring_reused.jpg"
    else:
        p_url = "/static/images/front_collision.jpg"

    claim = Claim(
        claim_id=cid,
        policy_id=pol_id,
        claimant_id=req.claimant_id or f"CUS-{rnd.randint(10000, 99999)}",
        workshop_id=req.workshop_id,
        bank_account=req.bank_account or f"SYN-ACC-U{rnd.randint(1000, 9999)}",
        phone=req.phone or f"SYN-PH-U{rnd.randint(1000, 9999)}",
        incident_date=inc_date,
        filed_date=fld_date,
        damage_type=clean_damage_type,
        amount_claimed=req.amount_claimed,
        narrative=req.narrative,
        photo_hash=photo_hash,
        photo_caption=caption,
        line_items=items,
        source="custom",
        label="custom",
        photo_url=p_url
    )

    start_date = "2026-01-01" if req.policy_active else "2024-01-01"
    end_date = "2026-12-31" if req.policy_active else "2024-12-31"
    pol = {"policy_id": pol_id, "start_date": start_date, "end_date": end_date, "coverage_limit": 25000.0}
    repo.add_claim(claim, policy=pol)

    case = _store(analyze(claim, repo))
    return {"claim": claim.model_dump(mode="json"), "case": case}


@app.post("/api/cases/analyze")
def analyze_claim(req: AnalyzeRequest):
    if req.claim:
        repo.add_claim(req.claim)
        claim = req.claim
    elif req.claim_id:
        claim = repo.get_claim(req.claim_id)
    else:
        claim = None
    if not claim:
        raise HTTPException(404, "Claim not found. Send claim_id or a full claim.")
    return _store(analyze(claim, repo))


@app.get("/api/cases/{case_id}")
def get_case(case_id: str):
    case = repo.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    return case


@app.post("/api/cases/{case_id}/decision")
def human_decision(case_id: str, req: DecisionRequest):
    if req.action not in ("approve", "override", "escalate"):
        raise HTTPException(422, "action must be approve, override or escalate")
    if not repo.get_case(case_id):
        raise HTTPException(404, "Case not found")
    repo.add_audit(case_id, "adjuster", req.action, {"note": req.note})
    return {"ok": True, "audit": repo.get_audit(case_id)}


@app.get("/api/cases/{case_id}/audit")
def audit(case_id: str):
    return repo.get_audit(case_id)


@app.post("/api/cases/{case_id}/copilot/questions")
def copilot_questions(case_id: str):
    raw = repo.get_case(case_id)
    if not raw:
        raise HTTPException(404, "Case not found")
    case_obj = CaseResult.model_validate(raw)
    payload, source = copilot.generate_questions(case_obj)
    return {
        "case_id": case_id,
        "claim_id": case_obj.claim.claim_id,
        "source": source,
        "questions": [q.model_dump() for q in payload.questions]
    }


@app.post("/api/cases/{case_id}/copilot/evaluate")
def copilot_evaluate(case_id: str, req: CopilotEvaluateRequest):
    raw = repo.get_case(case_id)
    if not raw:
        raise HTTPException(404, "Case not found")
    case_obj = CaseResult.model_validate(raw)
    ev, source = copilot.evaluate_statement(case_obj, req.question, req.claimant_answer)
    repo.add_audit(case_id, "copilot", "evaluated_statement", {
        "question": req.question[:120],
        "score": ev.plausibility_score,
        "action": ev.recommended_siu_action
    })
    return {
        "case_id": case_id,
        "source": source,
        "plausibility_score": ev.plausibility_score,
        "credibility_assessment": ev.credibility_assessment,
        "deception_markers": ev.deception_markers,
        "recommended_siu_action": ev.recommended_siu_action,
        "audit": repo.get_audit(case_id)
    }


@app.post("/api/attacks/launch")
def launch(req: LaunchRequest):
    """Generate one synthetic attack and run the defender on it (the live demo button)."""
    try:
        attack = generate_attack(repo, req.attack_type, req.stealth, random.Random())
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    case = _store(analyze(attack.claim, repo))
    policy_info = get_policy_detail(attack.claim.policy_id)
    return {
        "attack": attack.model_dump(mode="json"),
        "case": case,
        "policy": policy_info,
        "caught": case["decision"]["recommendation"] != "fast_track"
    }


@app.post("/api/extract")
def extract(req: ExtractRequest):
    fields, source = intake.extract_fields(req.text)
    return {
        "fields": fields.model_dump(),
        "source": source,
        "note": "Extracted via Gemini 2.5 on Vertex AI" if source == "gemini" else "Extracted via rule-based document intelligence (Mock fallback mode)"
    }


def _arena_worker(per_type: int, n_legit: int):
    try:
        def progress(done, total):
            ARENA.update(done=done, total=total)
        runner.run_arena(repo, per_type, n_legit, progress=progress)
        ARENA["status"] = "done"
    except Exception as exc:  # noqa: BLE001
        ARENA.update(status="error", error=str(exc))


@app.post("/api/arena/run")
def arena_run(req: ArenaRequest):
    with _arena_lock:
        if ARENA["status"] == "running":
            raise HTTPException(409, "Arena already running")
        ARENA.update(status="running", done=0, total=0, error=None)
    threading.Thread(target=_arena_worker, args=(min(req.per_type, 20), min(req.n_legit, 100)), daemon=True).start()
    return ARENA


@app.get("/api/arena/status")
def arena_status():
    return ARENA


@app.get("/api/arena/latest")
def arena_latest():
    return runner.load_latest() or {}


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
