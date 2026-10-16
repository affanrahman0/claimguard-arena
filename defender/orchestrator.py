"""Runs the defender agents in order and returns one CaseResult."""
import uuid

from shared import llm
from shared.schemas import CaseResult, Claim
from defender.agents import decision, fraud, intake, policy


def analyze(claim: Claim, repo) -> CaseResult:
    events = []
    _, ev = intake.run(claim)
    events.append(ev)
    pol, ev = policy.run(repo, claim)
    events.append(ev)
    fr, ev, _ = fraud.run(repo, claim)
    events.append(ev)
    dec, ev, _ = decision.run(claim, pol, fr)
    events.append(ev)
    return CaseResult(case_id=uuid.uuid4().hex[:8], claim=claim, events=events, policy=pol, fraud=fr,
                      decision=dec, llm_mode=llm.mode())
