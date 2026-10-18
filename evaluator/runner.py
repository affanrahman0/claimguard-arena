"""Arena: run attacks + honest claims + known ring claims through the defender and score it.
CLI:  python -m evaluator.runner --per-type 8 --legit 40"""
import argparse
import json
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Callable, Optional

from shared import config, llm
from shared.schemas import Improvement
from shared.store import SqliteRepo
from attacker.generator import generate_batch
from defender.orchestrator import analyze
from evaluator import metrics

DECOY = "W005"


def _suggest(row: dict) -> str:
    canned = metrics.SUGGESTIONS.get(row["attack_type"], "Review the thresholds for this signal.")
    prompt = (f"A fraud detector missed a synthetic '{row['attack_type']}' test claim (stealth variant: {row['stealth']}). "
              f"Signals it found: {row['signals'] or 'none'}. Suggest ONE concrete new check, in one sentence.")
    return llm.generate_json(prompt, Improvement, lambda: Improvement(suggestion=canned), system="You are a fraud-analytics lead.")[0].suggestion


def build_testset(repo, per_type: int, n_legit: int, rnd: random.Random) -> list[dict]:
    items = []
    for a in generate_batch(repo, per_type, rnd):
        items.append({"kind": "attack", "claim": a.claim, "attack_type": a.attack_type, "stealth": a.stealth, "decoy": False})
    for c in repo.sample_claims(10, rnd, workshop=DECOY):
        items.append({"kind": "legit", "claim": c, "attack_type": "", "stealth": False, "decoy": True})
    for c in repo.sample_claims(max(n_legit - 10, 0), rnd, not_workshops=(DECOY,)):
        items.append({"kind": "legit", "claim": c, "attack_type": "", "stealth": False, "decoy": False})
    for c in repo.sample_claims(50, rnd, label="ring"):
        items.append({"kind": "ring", "claim": c, "attack_type": "", "stealth": False, "decoy": False})
    return items


def run_arena(repo, per_type: int = 8, n_legit: int = 40, seed: int = 7, workers: int = 4,
              progress: Optional[Callable[[int, int], None]] = None, save: bool = True) -> dict:
    rnd = random.Random(seed)
    items = build_testset(repo, per_type, n_legit, rnd)
    done = {"n": 0}

    def work(it: dict) -> dict:
        case = analyze(it["claim"], repo)
        done["n"] += 1
        if progress:
            progress(done["n"], len(items))
        d = case.decision
        pol = repo.get_policy(it["claim"].policy_id)
        if not pol:
            pol = {
                "policy_id": it["claim"].policy_id,
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "coverage_limit": 25000.0,
            }
        return {"kind": it["kind"], "claim_id": it["claim"].claim_id, "attack_type": it["attack_type"], "stealth": it["stealth"],
                "decoy": it["decoy"], "risk_score": d.risk_score, "recommendation": d.recommendation,
                "flagged": d.recommendation != "fast_track",
                "signals": [s.type for s in case.policy.signals + case.fraud.signals],
                "claim": it["claim"].model_dump(mode="json"),
                "policy": pol}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(work, items))
    result = metrics.summarize(rows, {"per_type": per_type, "n_legit": n_legit, "seed": seed}, llm.mode(), _suggest)
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    if save:
        config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        (config.RESULTS_DIR / "latest.json").write_text(json.dumps(result, indent=2))
    return result


def load_latest() -> Optional[dict]:
    f = config.RESULTS_DIR / "latest.json"
    return json.loads(f.read_text()) if f.exists() else None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-type", type=int, default=8)
    ap.add_argument("--legit", type=int, default=40)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    res = run_arena(SqliteRepo(), args.per_type, args.legit, args.seed)
    print(f"LLM mode: {res['llm_mode']}")
    for t, a in res["attacks"].items():
        print(f"  {t:20s} caught {a['caught']}/{a['total']}  (stealth {a['stealth_caught']}/{a['stealth_total']})")
    print(f"Overall catch rate: {res['overall_catch_rate']:.0%}")
    print(f"False-positive rate on honest claims: {res['legit']['false_positive_rate']:.0%}  "
          f"| decoy workshop cleared: {res['decoy']['cleared']}/{res['decoy']['total']}  "
          f"| ring recall: {res['ring']['flagged']}/{res['ring']['total']}")
    print("Saved to evaluator/results/latest.json")
