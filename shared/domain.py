"""Insurance domain knowledge shared by the dataset generator, defender and attacker.
All of this is synthetic and simplified."""
import random
import re

INSURED_TYPES = ["collision", "glass", "vandalism", "theft", "fire", "flood"]
TYPE_WEIGHTS = [50, 15, 10, 8, 5, 6]
EXCLUDED_TYPES = {"wear_and_tear", "mechanical_breakdown"}

MEDIAN_AMOUNT = {
    "collision": 2400.0, "glass": 450.0, "vandalism": 900.0, "theft": 8000.0,
    "fire": 6000.0, "flood": 5000.0, "wear_and_tear": 300.0, "mechanical_breakdown": 1800.0,
}

PARTS = {
    "collision": {
        "front": ["Front bumper replacement", "Headlamp assembly", "Bonnet repair", "Radiator support", "Front fender repair"],
        "rear": ["Rear bumper replacement", "Tail lamp assembly", "Boot lid repair", "Rear panel repair"],
        "side": ["Door panel repair", "Side mirror replacement", "Quarter panel repair"],
        "generic": ["Paint and refinishing", "Labour charges"],
    },
    "glass": {"generic": ["Windshield replacement", "Side window replacement", "Glass fitting labour"]},
    "vandalism": {"generic": ["Paint respray", "Scratch removal", "Mirror replacement", "Window replacement"]},
    "theft": {"generic": ["Total loss settlement", "Recovery and towing"]},
    "fire": {"generic": ["Wiring harness replacement", "Interior refurbishment", "Paint and refinishing", "Towing"]},
    "flood": {"generic": ["Engine flush and repair", "Electrical system replacement", "Upholstery replacement", "Towing"]},
    "wear_and_tear": {"generic": ["Brake pad replacement", "Tyre replacement"]},
    "mechanical_breakdown": {"generic": ["Gearbox repair", "Engine overhaul"]},
}

UNRELATED_ITEMS = ["Engine overhaul", "Air-conditioning compressor", "Alloy wheel set", "Infotainment system replacement", "Suspension rebuild"]

NARRATIVES = {
    "front": [
        "I braked late in traffic and hit the vehicle ahead; the front of my car took the impact.",
        "While pulling out of a junction I struck a bollard with the front of the vehicle.",
    ],
    "rear": [
        "My car was stationary at a traffic light when another driver hit it from behind; the rear of the car took the impact.",
        "I was reversing out of a parking bay and the rear of my car struck a pillar.",
    ],
    "side": [
        "Another vehicle scraped along the side of my car while overtaking on a narrow road.",
        "A passing van clipped the side of my car in a car park.",
    ],
    "glass": ["A stone thrown up on the highway hit the windshield and cracked it."],
    "vandalism": ["I returned to the car park and found the car scratched and a mirror broken."],
    "theft": ["My vehicle was stolen from the car park overnight."],
    "fire": ["A fire started in the engine bay while the car was parked."],
    "flood": ["My car was parked in a basement that flooded during heavy rain."],
    "wear_and_tear": ["The brakes and tyres have worn out over time and need replacing."],
    "mechanical_breakdown": ["The gearbox failed while I was driving normally."],
}
VAGUE_NARRATIVE = "Another vehicle hit my car. I reported it the same day."

DIR_PATTERNS = {
    "front": r"\b(front|bonnet|headlamp|radiator)\b",
    "rear": r"\b(rear|boot|tail)\b",
    "side": r"\b(side|door|quarter)\b",
}

CLAUSES = {
    "3.1": "Accidental damage (collision) to the insured vehicle is covered.",
    "3.2": "Theft and attempted theft are covered.",
    "3.3": "Fire, flood, glass breakage and malicious damage are covered.",
    "4.1": "Wear and tear and gradual deterioration are excluded.",
    "4.2": "Mechanical or electrical breakdown not caused by an insured event is excluded.",
    "5.1": "Cover applies only to incidents occurring within the policy period.",
    "5.2": "The insurer's liability per claim is limited to the coverage limit in the schedule.",
}
COVER_CLAUSE = {"collision": "3.1", "theft": "3.2", "glass": "3.3", "fire": "3.3", "flood": "3.3", "vandalism": "3.3"}
EXCLUSION_CLAUSE = {"wear_and_tear": "4.1", "mechanical_breakdown": "4.2"}


def catalog(damage_type: str) -> set[str]:
    return {d.lower() for group in PARTS.get(damage_type, {}).values() for d in group}


def direction_of(text: str) -> set[str]:
    t = text.lower()
    return {d for d, pat in DIR_PATTERNS.items() if re.search(pat, t)}


def make_items(dtype: str, total: float, rnd: random.Random, direction: str | None = None) -> list[dict]:
    groups = PARTS[dtype]
    if dtype == "collision":
        direction = direction or rnd.choice(["front", "rear", "side"])
        first = rnd.choice(groups[direction])
        pool = [d for d in groups[direction] + groups["generic"] if d != first]
        chosen = [first] + rnd.sample(pool, min(len(pool), rnd.randint(1, 3)))
    else:
        pool = [d for g in groups.values() for d in g]
        chosen = rnd.sample(pool, min(len(pool), rnd.randint(2, 3)))
    weights = [rnd.uniform(0.5, 1.5) for _ in chosen]
    s = sum(weights)
    amounts = [round(total * w / s, 2) for w in weights]
    amounts[-1] = round(total - sum(amounts[:-1]), 2)
    return [{"description": d, "amount": a} for d, a in zip(chosen, amounts)]


def make_narrative(dtype: str, direction: str | None, rnd: random.Random) -> str:
    key = direction if dtype == "collision" else dtype
    return rnd.choice(NARRATIVES[key])


def make_caption(dtype: str, direction: str | None) -> str:
    if dtype == "collision":
        return f"Photo shows damage to the {direction} of the vehicle."
    return f"Photo shows {dtype.replace('_', ' ')} damage to the vehicle."
