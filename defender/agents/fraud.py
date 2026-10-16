"""Fraud agent: link analysis + arithmetic checks + a Gemini consistency review."""
import time

from shared import domain, llm
from shared.schemas import AgentEvent, ConsistencyFinding, FraudResult, Signal
from defender.tools import arithmetic, link_analysis


def _heuristic_consistency(claim) -> ConsistencyFinding:
    """Rule-based fallback / mock used when Gemini is not available."""
    issues = []
    cat = domain.catalog(claim.damage_type)
    for it in claim.line_items:
        if it.description.lower() not in cat:
            issues.append(f"Line item '{it.description}' is not typical for a {claim.damage_type} claim.")
    if claim.damage_type == "collision":
        n, p = domain.direction_of(claim.narrative), domain.direction_of(claim.photo_caption)
        i = set().union(*[domain.direction_of(x.description) for x in claim.line_items]) if claim.line_items else set()
        if n and i and not (n & i):
            issues.append(f"Narrative describes a {'/'.join(sorted(n))} impact but the repair items relate to the {'/'.join(sorted(i))}.")
        if p and i and not (p & i):
            issues.append(f"Photo caption shows {'/'.join(sorted(p))} damage but the repair items relate to the {'/'.join(sorted(i))}.")
    return ConsistencyFinding(consistent=not issues, issues=issues, confidence=0.7)


def _consistency(claim) -> tuple[ConsistencyFinding, str]:
    items = "\n".join(f"- {i.description}: {i.amount:,.2f}" for i in claim.line_items)
    prompt = (
        "You are an experienced motor-insurance claims investigator. Check whether the claim story, the photo "
        "description and the repair estimate are consistent with each other and with the damage type.\n"
        f"Damage type: {claim.damage_type}\nNarrative: {claim.narrative}\nPhoto description: {claim.photo_caption}\n"
        f"Repair estimate lines:\n{items}\n\n"
        "Report only genuine inconsistencies (e.g. impact side differs, items unrelated to the damage). "
        "If everything fits, set consistent=true and issues=[]. Give confidence 0-1."
    )
    return llm.generate_json(prompt, ConsistencyFinding, lambda: _heuristic_consistency(claim),
                             system="You are a careful fraud investigator. Do not invent facts.")


def run(repo, claim) -> tuple[FraudResult, AgentEvent, str]:
    t = time.time()
    links = link_analysis.find_links(repo, claim)
    signals, note = link_analysis.link_signals(claim, links)
    signals += arithmetic.check_totals(claim)
    signals += arithmetic.check_outlier(repo, claim)
    cons, src = _consistency(claim)
    if not cons.consistent and cons.issues:
        signals.append(Signal(type="narrative_estimate_mismatch", severity="high", weight=30, evidence=" ".join(cons.issues)))
    nodes, edges = link_analysis.build_graph(claim, links)
    res = FraudResult(signals=signals, nodes=nodes, edges=edges, consistency=cons, baseline_note=note)
    n_linked = len({n.id for n in nodes if n.kind == "claim_linked"})
    summary = (f"Found {len(signals)} signal(s); linked to {n_linked} other claim(s). " if signals else "No fraud signals found. ") + note
    ev = AgentEvent(agent="Fraud", summary=summary, detail={"signals": [s.type for s in signals], "llm_source": src, "linked_claims": n_linked},
                    ms=int((time.time() - t) * 1000))
    return res, ev, src
