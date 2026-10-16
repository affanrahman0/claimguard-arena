"""Adversary: generates SYNTHETIC, clearly-labelled attack claims to test the defender.
Each attack type has a normal variant and a 'stealth' variant that is deliberately subtler.
All outputs carry source='adversary' and a claim_id starting with 'ATK-'. Sandbox use only."""
import random
from datetime import timedelta

from shared import domain, llm
from shared.schemas import AttackCase, AttackNarrative, Claim, LineItem

ATTACK_TYPES = ["narrative_mismatch", "estimate_inflation", "invoice_tamper", "clone_and_tweak"]


def _new_id(kind: str, rnd: random.Random) -> str:
    return f"ATK-{kind[:5].upper()}-{rnd.randint(1000, 9999)}"


def _rescale(items: list[LineItem], new_total: float) -> list[LineItem]:
    old = sum(i.amount for i in items) or 1.0
    scaled = [round(i.amount * new_total / old, 2) for i in items]
    scaled[-1] = round(new_total - sum(scaled[:-1]), 2)
    return [LineItem(description=i.description, amount=a) for i, a in zip(items, scaled)]


def _fresh_identity(rnd: random.Random) -> dict:
    """A brand-new claimant identity, so only the intended weakness is detectable."""
    n = rnd.randint(100000, 999999)
    return {"claimant_id": f"CUS-X{n}", "bank_account": f"SYN-ACC-X{n}", "phone": f"SYN-PH-X{n}",
            "photo_hash": f"{rnd.getrandbits(64):016x}"}


def _opposite(direction: str) -> str:
    return {"front": "rear", "rear": "front", "side": "front"}[direction]


def narrative_mismatch(base: Claim, rnd: random.Random, stealth: bool) -> AttackCase:
    items_dir = set().union(*[domain.direction_of(i.description) for i in base.line_items]) or {"front"}
    true_dir = sorted(items_dir)[0]
    wrong = _opposite(true_dir)
    if stealth:
        text = domain.VAGUE_NARRATIVE  # no impact direction: hard to contradict
    else:
        fallback = lambda: AttackNarrative(narrative=domain.make_narrative("collision", wrong, rnd))
        prompt = (f"Write a 2-sentence first-person narrative for a SYNTHETIC test insurance claim in which a car "
                  f"is hit on the {wrong} of the vehicle. Mention the word '{wrong}'.")
        text = llm.generate_json(prompt, AttackNarrative, fallback, system="You write synthetic test data.", temperature=0.7)[0].narrative
    claim = base.model_copy(update={"claim_id": _new_id("narr", rnd), "narrative": text, "source": "adversary",
                                    "label": "attack:narrative_mismatch", **_fresh_identity(rnd)})
    return AttackCase(claim=claim, attack_type="narrative_mismatch", stealth=stealth,
                      intent="Story describes a different impact than the photo and repair lines." if not stealth
                      else "Vague story that avoids committing to an impact side.")


def estimate_inflation(base: Claim, rnd: random.Random, stealth: bool, median: float) -> AttackCase:
    factor = rnd.uniform(1.55, 1.75) if stealth else rnd.uniform(2.3, 3.5)
    total = round(median * factor, 2)
    items = _rescale(base.line_items, total)
    if not stealth:
        extra = rnd.sample(domain.UNRELATED_ITEMS, 2)
        pad = round(total * 0.25, 2)
        items = _rescale(items, total - 2 * pad) + [LineItem(description=extra[0], amount=pad), LineItem(description=extra[1], amount=pad)]
    claim = base.model_copy(update={"claim_id": _new_id("infl", rnd), "amount_claimed": total, "line_items": items,
                                    "source": "adversary", "label": "attack:estimate_inflation", **_fresh_identity(rnd)})
    return AttackCase(claim=claim, attack_type="estimate_inflation", stealth=stealth,
                      intent="Padded estimate with unrelated parts." if not stealth else "Moderate inflation kept under the outlier threshold.")


def invoice_tamper(base: Claim, rnd: random.Random, stealth: bool) -> AttackCase:
    lines = sum(i.amount for i in base.line_items)
    total = round(lines * (1.01 if stealth else rnd.uniform(1.25, 1.8)), 2)
    claim = base.model_copy(update={"claim_id": _new_id("inv", rnd), "amount_claimed": total, "source": "adversary",
                                    "label": "attack:invoice_tamper", **_fresh_identity(rnd)})
    return AttackCase(claim=claim, attack_type="invoice_tamper", stealth=stealth,
                      intent="Claimed total is higher than the itemised lines." if not stealth else "Tiny total mismatch inside the tolerance.")


def clone_and_tweak(base: Claim, rnd: random.Random, stealth: bool) -> AttackCase:
    shift = timedelta(days=rnd.randint(5, 20))
    incident = base.incident_date + shift
    upd = {"claim_id": _new_id("clone", rnd), "incident_date": incident, "filed_date": incident + timedelta(days=3),
           "amount_claimed": round(base.amount_claimed * rnd.uniform(0.95, 1.05), 2), "source": "adversary",
           "label": "attack:clone_and_tweak"}
    if stealth:  # new photo, account and phone: only claimant + damage type remain linked
        upd.update(photo_hash=f"{rnd.getrandbits(64):016x}", bank_account=f"SYN-ACC-X{rnd.randint(100000, 999999)}",
                   phone=f"SYN-PH-X{rnd.randint(100000, 999999)}")
    claim = base.model_copy(update=upd)
    claim.line_items = _rescale(claim.line_items, claim.amount_claimed)
    return AttackCase(claim=claim, attack_type="clone_and_tweak", stealth=stealth,
                      intent="Copy of an earlier claim with small changes." if not stealth else "Copy with new photo, account and phone.")
