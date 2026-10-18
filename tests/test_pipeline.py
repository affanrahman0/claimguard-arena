import os
os.environ["LLM_MODE"] = "mock"
import random

import pytest
from fastapi.testclient import TestClient

from shared import dataset
from shared.store import SqliteRepo
from attacker.generator import ATTACK_TYPES, generate_attack
from defender.orchestrator import analyze
from evaluator.runner import run_arena


@pytest.fixture(scope="session")
def repo(tmp_path_factory):
    path = tmp_path_factory.mktemp("db") / "test.db"
    dataset.build(path)
    return SqliteRepo(path)


def test_ring_and_decoy_exist(repo):
    assert repo.workshop_info("W017")["linked_count"] == 11
    assert repo.workshop_info("W005")["linked_count"] == 0


def test_clean_and_decoy_claims_fast_track(repo):
    for cid in ("CLM-HERO-CLEAN", "CLM-HERO-DECOY"):
        assert analyze(repo.get_claim(cid), repo).decision.recommendation == "fast_track"


def test_ring_claims_flagged_and_graph_built(repo):
    case = analyze(repo.get_claim("CLM-RING-005"), repo)
    assert case.decision.recommendation == "escalate"
    assert sum(n.kind == "claim_linked" for n in case.fraud.nodes) >= 5


def test_policy_violations_flagged(repo):
    for cid in ("CLM-HERO-LAPSED", "CLM-HERO-EXCLUDED"):
        assert analyze(repo.get_claim(cid), repo).decision.recommendation != "fast_track"


@pytest.mark.parametrize("attack_type", ATTACK_TYPES)
def test_normal_attacks_are_caught(repo, attack_type):
    attack = generate_attack(repo, attack_type, False, random.Random(3))
    assert attack.claim.claim_id.startswith("ATK-") and attack.claim.source == "adversary"
    assert analyze(attack.claim, repo).decision.recommendation != "fast_track"


def test_arena_runs_and_has_no_false_positives(repo):
    res = run_arena(repo, per_type=4, n_legit=20, workers=2, save=False)
    assert res["legit"]["false_positive_rate"] == 0
    assert res["ring"]["recall"] == 1
    assert 0 < res["overall_catch_rate"] <= 1


def test_api_endpoints(repo, monkeypatch):
    import app.main as m
    monkeypatch.setattr(m, "repo", repo)
    with TestClient(m.app) as client:
        assert client.get("/api/health").json()["status"] == "ok"
        r = client.post("/api/cases/analyze", json={"claim_id": "CLM-RING-005"}).json()
        assert r["decision"]["recommendation"] == "escalate"
        d = client.post(f"/api/cases/{r['case_id']}/decision", json={"action": "approve", "note": "ok"}).json()
        assert d["ok"] and len(d["audit"]) == 2
        launch = client.post("/api/attacks/launch", json={"attack_type": "invoice_tamper"}).json()
        assert launch["caught"] is True
        assert "policy" in launch
        assert "product_tier" in launch["policy"]

        q_res = client.post(f"/api/cases/{r['case_id']}/copilot/questions").json()
        assert len(q_res["questions"]) == 3
        assert "target_signal" in q_res["questions"][0]

        eval_res = client.post(f"/api/cases/{r['case_id']}/copilot/evaluate", json={
            "question": q_res["questions"][0]["question"],
            "claimant_answer": "The repair shop handled the photos and paperwork on my behalf."
        }).json()
        assert 0 <= eval_res["plausibility_score"] <= 100
        assert len(eval_res["deception_markers"]) > 0

        assert client.get("/").status_code == 200
