"""Policy agent: check cover against the (synthetic) policy wording and cite clauses."""
import time

from shared import domain
from shared.schemas import AgentEvent, PolicyResult, Signal


def run(repo, claim) -> tuple[PolicyResult, AgentEvent]:
    t = time.time()
    pol = repo.get_policy(claim.policy_id)
    sigs: list[Signal] = []
    cites: list[str] = []
    if not pol:
        res = PolicyResult(covered=False, in_period=False, excluded=False, within_limit=False, citations=[],
                           explanation="Policy not found.",
                           signals=[Signal(type="policy_not_found", severity="high", weight=40, evidence="No policy matches this claim.")])
        return res, AgentEvent(agent="Policy", summary=res.explanation, ms=int((time.time() - t) * 1000))

    start, end = pol["start_date"], pol["end_date"]
    in_period = start <= claim.incident_date.isoformat() <= end
    cites.append("5.1")
    if not in_period:
        sigs.append(Signal(type="out_of_policy_period", severity="high", weight=40,
                           evidence=f"Incident on {claim.incident_date} is outside the policy period {start} to {end} (clause 5.1)."))

    excluded = claim.damage_type in domain.EXCLUDED_TYPES
    if excluded:
        clause = domain.EXCLUSION_CLAUSE[claim.damage_type]
        cites.append(clause)
        sigs.append(Signal(type="excluded_damage", severity="high", weight=30,
                           evidence=f"{claim.damage_type.replace('_', ' ').title()} is excluded under clause {clause}."))
    else:
        cites.append(domain.COVER_CLAUSE.get(claim.damage_type, "3.1"))

    within = claim.amount_claimed <= pol["coverage_limit"]
    cites.append("5.2")
    if not within:
        sigs.append(Signal(type="over_limit", severity="medium", weight=15,
                           evidence=f"Claimed {claim.amount_claimed:,.2f} exceeds the coverage limit {pol['coverage_limit']:,.0f} (clause 5.2)."))

    covered = in_period and not excluded and within
    cites = sorted(set(cites))
    expl = ("Covered: incident within period, damage type insured, amount within limit." if covered
            else "Not fully covered: " + " ".join(s.evidence for s in sigs))
    res = PolicyResult(covered=covered, in_period=in_period, excluded=excluded, within_limit=within,
                       citations=cites, explanation=expl, signals=sigs)
    return res, AgentEvent(agent="Policy", summary=expl, detail={"citations": cites}, ms=int((time.time() - t) * 1000))
