"""Turns raw per-claim results into the Arena scoreboard."""
SUGGESTIONS = {
    "narrative_mismatch": "Make Gemini compare narrative, photo and repair lines on every claim, and treat a story with no impact side as 'request more information'.",
    "estimate_inflation": "Benchmark each repair line against per-part price ranges instead of one median per damage type, and lower the outlier threshold for high-volume types.",
    "invoice_tamper": "Require itemised lines to sum exactly to the claimed total (zero tolerance) and flag any manual override of totals.",
    "clone_and_tweak": "Add fuzzy duplicate detection on claimant + damage type + date window, plus image-similarity matching so a retaken photo of the same damage is still linked.",
}


def summarize(rows: list[dict], config: dict, llm_mode: str, suggest) -> dict:
    attacks: dict = {}
    for r in rows:
        if r["kind"] != "attack":
            continue
        a = attacks.setdefault(r["attack_type"], {"total": 0, "caught": 0, "stealth_total": 0, "stealth_caught": 0})
        a["total"] += 1
        a["caught"] += r["flagged"]
        if r["stealth"]:
            a["stealth_total"] += 1
            a["stealth_caught"] += r["flagged"]
    for a in attacks.values():
        a["catch_rate"] = round(a["caught"] / a["total"], 3) if a["total"] else 0.0

    def group(kind, subset=None):
        rs = [r for r in rows if r["kind"] == kind and (subset is None or subset(r))]
        return rs

    atk = group("attack")
    legit = group("legit")
    decoy = [r for r in legit if r["decoy"]]
    ring = group("ring")
    misses = [dict(r, suggestion=suggest(r)) for r in atk if not r["flagged"]]
    return {
        "config": config, "llm_mode": llm_mode,
        "attacks": attacks,
        "overall_catch_rate": round(sum(r["flagged"] for r in atk) / len(atk), 3) if atk else 0.0,
        "legit": {"total": len(legit), "flagged": sum(r["flagged"] for r in legit),
                  "false_positive_rate": round(sum(r["flagged"] for r in legit) / len(legit), 3) if legit else 0.0},
        "decoy": {"total": len(decoy), "cleared": sum(not r["flagged"] for r in decoy),
                  "cleared_rate": round(sum(not r["flagged"] for r in decoy) / len(decoy), 3) if decoy else 0.0},
        "ring": {"total": len(ring), "flagged": sum(r["flagged"] for r in ring),
                 "recall": round(sum(r["flagged"] for r in ring) / len(ring), 3) if ring else 0.0},
        "misses": misses,
        "false_positives": [r for r in legit if r["flagged"]],
    }
