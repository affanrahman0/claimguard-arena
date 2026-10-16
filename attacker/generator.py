"""Public entry points for the attacker. The evaluator and the API only import from here."""
import random

from shared.schemas import AttackCase
from attacker import attacks
from attacker.attacks import ATTACK_TYPES


def generate_attack(repo, attack_type: str, stealth: bool, rnd: random.Random) -> AttackCase:
    if attack_type not in ATTACK_TYPES:
        raise ValueError(f"Unknown attack type: {attack_type}")
    dtype = "collision" if attack_type == "narrative_mismatch" else None
    pool = repo.sample_claims(1, rnd, damage_type=dtype, not_workshops=("W017",))
    if not pool:
        raise RuntimeError("No base claims available. Run: python -m shared.dataset")
    base = pool[0]
    if attack_type == "narrative_mismatch":
        return attacks.narrative_mismatch(base, rnd, stealth)
    if attack_type == "estimate_inflation":
        return attacks.estimate_inflation(base, rnd, stealth, repo.median_amount(base.damage_type))
    if attack_type == "invoice_tamper":
        return attacks.invoice_tamper(base, rnd, stealth)
    return attacks.clone_and_tweak(base, rnd, stealth)


def generate_batch(repo, per_type: int, rnd: random.Random) -> list[AttackCase]:
    """per_type attacks of every type; every 4th one is a stealth variant."""
    return [generate_attack(repo, t, i % 4 == 3, rnd) for t in ATTACK_TYPES for i in range(per_type)]
