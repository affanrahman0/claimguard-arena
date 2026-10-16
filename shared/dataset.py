"""Synthetic dataset generator. Run:  python -m shared.dataset

Creates data/claims.db with ~2000 normal claims, one busy-but-honest workshop (the DECOY),
one fraud ring planted at another workshop, and a few hero claims for demos.
Everything is synthetic. Seeded, so results are reproducible."""
import hashlib
import json
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from . import config, domain

SEED = 42
DECOY_WORKSHOP = "W005"
RING_WORKSHOP = "W017"

SCHEMA = """
DROP TABLE IF EXISTS claims; DROP TABLE IF EXISTS policies; DROP TABLE IF EXISTS workshops;
DROP TABLE IF EXISTS cases; DROP TABLE IF EXISTS audit_log;
CREATE TABLE claims (
  claim_id TEXT PRIMARY KEY, policy_id TEXT, claimant_id TEXT, workshop_id TEXT, bank_account TEXT,
  phone TEXT, incident_date TEXT, filed_date TEXT, damage_type TEXT, amount_claimed REAL,
  narrative TEXT, photo_hash TEXT, photo_caption TEXT, line_items TEXT, source TEXT, label TEXT, photo_url TEXT);
CREATE INDEX ix_bank ON claims(bank_account); CREATE INDEX ix_phone ON claims(phone);
CREATE INDEX ix_photo ON claims(photo_hash); CREATE INDEX ix_ws ON claims(workshop_id);
CREATE INDEX ix_claimant ON claims(claimant_id);
CREATE TABLE policies (policy_id TEXT PRIMARY KEY, start_date TEXT, end_date TEXT, coverage_limit REAL);
CREATE TABLE workshops (workshop_id TEXT PRIMARY KEY, name TEXT);
CREATE TABLE cases (case_id TEXT PRIMARY KEY, claim_id TEXT, created_at TEXT, payload TEXT);
CREATE TABLE audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT, ts TEXT, actor TEXT, event TEXT, detail TEXT);
"""


def _photo(claim_id: str) -> str:
    return hashlib.md5(f"{claim_id}-photo".encode()).hexdigest()[:16]


def _entities(idx: int) -> dict:
    return {"claimant_id": f"CUS-{idx:06d}", "bank_account": f"SYN-ACC-{idx:06d}", "phone": f"SYN-PH-{idx:06d}"}


def _make_claim(claim_id, idx, workshop, dtype, rnd, incident, *, label="legit", source="history",
                factor=None, direction=None, bank=None, phone=None, photo=None):
    if dtype == "collision":
        direction = direction or rnd.choice(["front", "rear", "side"])
    f = factor or min(1.6, max(0.6, rnd.lognormvariate(0, 0.25)))
    total = round(domain.MEDIAN_AMOUNT[dtype] * f, 2)
    ent = _entities(idx)
    return {
        "claim_id": claim_id, "policy_id": f"POL-{claim_id}", "claimant_id": ent["claimant_id"],
        "workshop_id": workshop, "bank_account": bank or ent["bank_account"], "phone": phone or ent["phone"],
        "incident_date": incident.isoformat(), "filed_date": (incident + timedelta(days=rnd.randint(1, 20))).isoformat(),
        "damage_type": dtype, "amount_claimed": total, "narrative": domain.make_narrative(dtype, direction, rnd),
        "photo_hash": photo or _photo(claim_id), "photo_caption": domain.make_caption(dtype, direction),
        "line_items": json.dumps(domain.make_items(dtype, total, rnd, direction)), "source": source, "label": label,
    }


def _policy(claim_id, incident, rnd, start_offset=None):
    start = incident - timedelta(days=start_offset if start_offset is not None else rnd.randint(10, 300))
    return (f"POL-{claim_id}", start.isoformat(), (start + timedelta(days=364)).isoformat(), 20000.0)


def build(path: Path = None, seed: int = SEED, n_history: int = 2000) -> Path:
    path = Path(path or config.DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    rnd = random.Random(seed)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    claims, policies = [], []

    # ---- workshops
    names = ["Auto", "Motors", "Garage", "Car Care", "Body Works"]
    prefix = ["Prime", "Metro", "Eagle", "Summit", "Harbour", "Orbit", "Nova", "Pioneer"]
    workshops = {f"W{i:03d}": f"{rnd.choice(prefix)} {rnd.choice(names)}" for i in range(1, 41)}
    workshops[DECOY_WORKSHOP] = "CityFix Motors"
    workshops[RING_WORKSHOP] = "Apex Auto Works"

    # ---- normal history
    others = [w for w in workshops if w not in (DECOY_WORKSHOP, RING_WORKSHOP)]
    assign = [DECOY_WORKSHOP] * 90 + [RING_WORKSHOP] * 25 + [rnd.choice(others) for _ in range(n_history - 115)]
    rnd.shuffle(assign)
    claimant_types: dict[int, set] = {}
    next_idx = 1
    for i, ws in enumerate(assign, start=1):
        cid = f"CLM-{i:05d}"
        repeat = claimant_types and rnd.random() < 0.05
        if repeat:
            idx = rnd.choice(list(claimant_types))
            free = [t for t in domain.INSURED_TYPES if t not in claimant_types[idx]]
            if not free:
                repeat = False
        if repeat:
            dtype = rnd.choice(free)
        else:
            idx, next_idx = next_idx, next_idx + 1
            dtype = rnd.choices(domain.INSURED_TYPES, domain.TYPE_WEIGHTS)[0]
        claimant_types.setdefault(idx, set()).add(dtype)
        incident = date(2025, 11, 1) + timedelta(days=rnd.randint(0, 330))
        claims.append(_make_claim(cid, idx, ws, dtype, rnd, incident))
        policies.append(_policy(cid, incident, rnd))

    # ---- planted fraud ring: 11 claims, 1 workshop, 3 shared accounts/phones, 2 reused photos
    accounts = [f"SYN-ACC-R{i:03d}" for i in range(1, 4)]
    phones = [f"SYN-PH-R{i:03d}" for i in range(1, 4)]
    reused = {1: "a1b2c3d4e5f60718", 4: "a1b2c3d4e5f60718", 2: "9f8e7d6c5b4a3921", 7: "9f8e7d6c5b4a3921", 9: "9f8e7d6c5b4a3921"}
    for k in range(11):
        cid = f"CLM-RING-{k + 1:03d}"
        incident = date(2026, 5, 20) + timedelta(days=rnd.randint(0, 100))
        dtype = "collision" if k % 4 else "glass"
        claims.append(_make_claim(cid, 5000 + k, RING_WORKSHOP, dtype, rnd, incident, label="ring",
                                  bank=accounts[k % 3], phone=phones[(k + 1) % 3], photo=reused.get(k)))
        policies.append(_policy(cid, incident, rnd))

    # ---- hero claims for demos
    inc = date(2026, 6, 14)
    heroes = [
        ("CLM-HERO-CLEAN", 9001, "W010", "collision", {}, "legit", None),
        ("CLM-HERO-DECOY", 9002, DECOY_WORKSHOP, "collision", {}, "legit", None),
        ("CLM-HERO-LAPSED", 9003, "W021", "collision", {}, "policy_violation", -25),
        ("CLM-HERO-EXCLUDED", 9004, "W012", "wear_and_tear", {}, "policy_violation", None),
    ]
    for cid, idx, ws, dtype, kw, label, offset in heroes:
        claims.append(_make_claim(cid, idx, ws, dtype, rnd, inc, label=label, source="hero", **kw))
        policies.append(_policy(cid, inc, rnd, start_offset=offset))

    conn.executemany("INSERT INTO workshops VALUES (?,?)", workshops.items())
    cols = ["claim_id", "policy_id", "claimant_id", "workshop_id", "bank_account", "phone", "incident_date",
            "filed_date", "damage_type", "amount_claimed", "narrative", "photo_hash", "photo_caption",
            "line_items", "source", "label"]
    conn.executemany(f"INSERT INTO claims ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                     [[c[k] for k in cols] for c in claims])
    conn.executemany("INSERT INTO policies VALUES (?,?,?,?)", policies)
    conn.commit()
    conn.close()
    return path


if __name__ == "__main__":
    p = build()
    print(f"Synthetic dataset written to {p}")
