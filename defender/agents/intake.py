"""Intake agent: validate and normalise the claim. Optionally extract fields from free text with Gemini."""
import time

from shared import llm
from shared.schemas import AgentEvent, Claim, ExtractedFields


def run(claim: Claim) -> tuple[list[str], AgentEvent]:
    t = time.time()
    notes = []
    if claim.filed_date < claim.incident_date:
        notes.append("Filed date is before the incident date.")
    if not claim.line_items:
        notes.append("No itemised lines supplied.")
    if not claim.photo_hash:
        notes.append("No photo supplied.")
    summary = f"Read claim {claim.claim_id}: {claim.damage_type}, {claim.amount_claimed:,.2f}, workshop {claim.workshop_id}."
    if notes:
        summary += " Notes: " + " ".join(notes)
    return notes, AgentEvent(agent="Intake", summary=summary, detail={"notes": notes, "items": len(claim.line_items)},
                             ms=int((time.time() - t) * 1000))


def _heuristic_extract(raw_text: str) -> ExtractedFields:
    import re
    from shared import domain
    pol = re.search(r"\b(POL-[A-Za-z0-9_-]+)\b", raw_text)
    inc = re.search(r"\b(202\d-[01]\d-[0-3]\d)\b", raw_text)
    amt = re.search(r"\$\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)|(?:amount|cost|total)[:\s]+\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)", raw_text, re.IGNORECASE)
    amt_val = 0.0
    if amt:
        val = (amt.group(1) or amt.group(2) or "").replace(",", "").strip()
        try:
            amt_val = float(val)
        except ValueError:
            pass
    dtype = ""
    for dt in domain.INSURED_TYPES + list(domain.EXCLUDED_TYPES):
        if dt.replace("_", " ") in raw_text.lower() or dt in raw_text.lower():
            dtype = dt
            break
    if not dtype and "dent" in raw_text.lower():
        dtype = "collision"
    ws = re.search(r"\b(W\d{3})\b", raw_text)
    acc = re.search(r"\b(SYN-ACC-[A-Za-z0-9_-]+)\b", raw_text)
    ph = re.search(r"\b(SYN-PH-[A-Za-z0-9_-]+|\+?1?\s*\(?[0-9]{3}\)?[-. ]?[0-9]{3}[-. ]?[0-9]{4})\b", raw_text)
    return ExtractedFields(
        policy_id=pol.group(1) if pol else "POL-CLM-AUTO",
        incident_date=inc.group(1) if inc else "2026-06-15",
        amount_claimed=amt_val or 1850.0,
        damage_type=dtype or "collision",
        workshop_id=ws.group(1) if ws else "W010",
        bank_account=acc.group(1) if acc else "SYN-ACC-NEW01",
        phone=ph.group(1) if ph else "SYN-PH-NEW01",
        narrative=raw_text.strip()[:600] or "Reported vehicle collision damage."
    )


def extract_fields(raw_text: str) -> tuple[ExtractedFields, str]:
    """Free-text claim form -> structured fields (Gemini or pattern fallback)."""
    from shared import domain
    prompt = ("Extract the claim fields from this motor insurance claim form text. "
              "Allowed damage_type values MUST be one of: 'collision', 'glass', 'vandalism', 'theft', 'fire', 'flood', 'wear_and_tear', 'mechanical_breakdown'. "
              "Use ISO dates (YYYY-MM-DD). If a field is missing use an empty string or 0.\n\n" + raw_text)
    fields, source = llm.generate_json(prompt, ExtractedFields, lambda: _heuristic_extract(raw_text),
                                       system="You extract structured data. Return only the JSON.")
    fields.damage_type = domain.normalize_damage_type(fields.damage_type)
    return fields, source
