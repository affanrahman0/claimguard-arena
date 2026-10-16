"""Decision agent: transparent score from the signals + a plain-language explanation."""
import time

from shared import config, llm
from shared.schemas import AgentEvent, Decision, ReasoningOut


def recommend(score: int) -> str:
    if score < config.THRESH_INVESTIGATE:
        return "fast_track"
    return "investigate" if score <= config.THRESH_ESCALATE else "escalate"


def run(claim, policy, fraud) -> tuple[Decision, AgentEvent, str]:
    t = time.time()
    signals = sorted(policy.signals + fraud.signals, key=lambda s: -s.weight)
    score = min(100, sum(s.weight for s in signals))
    rec = recommend(score)
    evidence = [s.evidence for s in signals]

    def mock() -> ReasoningOut:
        if not signals:
            return ReasoningOut(reasoning="No policy or fraud signals were found. The claim is consistent and can be fast-tracked.")
        top = "; ".join(f"{s.type.replace('_', ' ')} (+{s.weight})" for s in signals[:4])
        return ReasoningOut(reasoning=f"Risk score {score}/100 -> {rec.replace('_', ' ')}. Main drivers: {top}. A human adjuster should confirm.")

    prompt = (
        "Explain this claim decision to an insurance adjuster in 2-3 sentences. Use ONLY the facts below; do not add new facts.\n"
        f"Claim: {claim.claim_id}, {claim.damage_type}, amount {claim.amount_claimed:,.2f}\n"
        f"Risk score: {score}/100. Recommendation: {rec}.\nSignals:\n" + "\n".join(f"- {e}" for e in evidence)
    )
    out, src = llm.generate_json(prompt, ReasoningOut, mock, system="You write clear, factual claim summaries.", model=config.MODEL_REASON)
    dec = Decision(risk_score=score, recommendation=rec, reasoning=out.reasoning, evidence=evidence)
    ev = AgentEvent(agent="Decision", summary=f"Risk {score}/100 -> {rec.replace('_', ' ')}. {out.reasoning}",
                    detail={"score": score, "llm_source": src}, ms=int((time.time() - t) * 1000))
    return dec, ev, src
