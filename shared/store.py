"""Data access layer (SQLite). To move to BigQuery later, re-implement this one class."""
import hashlib
import json
import random
import sqlite3
import statistics
import threading
from datetime import datetime, timezone
from typing import Optional

from . import config, domain
from .schemas import Claim

_LINK_COLUMNS = {"bank_account", "phone", "photo_hash"}
_LINKED_SQL = """
SELECT c.claim_id FROM claims c WHERE c.workshop_id=? AND EXISTS (
  SELECT 1 FROM claims o WHERE o.claim_id!=c.claim_id AND o.workshop_id=c.workshop_id
  AND (o.bank_account=c.bank_account OR o.phone=c.phone OR o.photo_hash=c.photo_hash))"""


def resolve_photo_url(claim_id: str, damage_type: str, narrative: str = "", photo_hash: str = "") -> str:
    # 1. Flagged Fraud Ring claims deliberately share the exact same reused photo
    if photo_hash in ("a1b2c3d4e5f60718", "9f8e7d6c5b4a3921") or "RING" in claim_id:
        return "/static/images/ring_reused.jpg"
    
    text = (narrative or "").lower()
    dtype = (damage_type or "").lower()
    
    # 2. Specific damage types
    if dtype == "wear_and_tear" or "tyre" in text or "brake" in text:
        return "/static/images/wear_and_tear.jpg"
    if dtype in ("vandalism", "theft", "fire") or "scratch" in text or "key" in text or "spray" in text:
        return "/static/images/vandalism_scratch.jpg"
    if dtype in ("glass", "windshield") or "windshield" in text or "stone chip" in text or "crack" in text:
        return "/static/images/glass_crack.jpg"
    if "side" in text or "door" in text or "flank" in text:
        return "/static/images/side_collision.jpg"
    if "rear" in text or "tail" in text or "boot" in text or "bumper rear" in text:
        return "/static/images/rear_collision.jpg"
    if "front" in text or "bonnet" in text or "grill" in text:
        return "/static/images/front_collision.jpg"

    # 3. Deterministic rotation across the 2,000 synthetic collision dataset so claims don't all look identical
    variants = [
        "/static/images/front_collision.jpg",
        "/static/images/rear_collision.jpg",
        "/static/images/side_collision.jpg",
    ]
    idx = int(hashlib.md5(claim_id.encode()).hexdigest(), 16) % len(variants)
    return variants[idx]


def _to_claim(row: sqlite3.Row) -> Claim:
    d = dict(row)
    d["line_items"] = json.loads(d["line_items"])
    if not d.get("photo_url"):
        d["photo_url"] = resolve_photo_url(d["claim_id"], d["damage_type"], d.get("narrative", ""), d.get("photo_hash", ""))
    return Claim(**d)


class SqliteRepo:
    def __init__(self, path=None):
        self.path = path or config.DB_PATH
        self._cache: dict = {}
        self._lock = threading.Lock()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def exists(self) -> bool:
        try:
            with self._conn() as c:
                return c.execute("SELECT COUNT(*) FROM claims").fetchone()[0] > 0
        except sqlite3.Error:
            return False

    # ---- claims & policies
    def get_claim(self, claim_id: str) -> Optional[Claim]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM claims WHERE claim_id=?", (claim_id,)).fetchone()
        return _to_claim(row) if row else None

    def get_policy(self, policy_id: str) -> Optional[dict]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM policies WHERE policy_id=?", (policy_id,)).fetchone()
        return dict(row) if row else None

    # ---- link analysis helpers
    def claims_sharing(self, column: str, value: str, exclude_id: str) -> list[dict]:
        if column not in _LINK_COLUMNS:
            raise ValueError(column)
        with self._conn() as c:
            rows = c.execute(f"SELECT claim_id, workshop_id, label FROM claims WHERE {column}=? AND claim_id!=?",
                             (value, exclude_id)).fetchall()
        return [dict(r) for r in rows]

    def same_claimant_same_type(self, claimant_id: str, damage_type: str, exclude_id: str) -> list[dict]:
        with self._conn() as c:
            rows = c.execute("SELECT claim_id FROM claims WHERE claimant_id=? AND damage_type=? AND claim_id!=?",
                             (claimant_id, damage_type, exclude_id)).fetchall()
        return [dict(r) for r in rows]

    def workshop_info(self, workshop_id: str) -> dict:
        key = ("ws", workshop_id)
        with self._lock:
            if key in self._cache:
                return self._cache[key]
        with self._conn() as c:
            name = c.execute("SELECT name FROM workshops WHERE workshop_id=?", (workshop_id,)).fetchone()
            count = c.execute("SELECT COUNT(*) FROM claims WHERE workshop_id=?", (workshop_id,)).fetchone()[0]
            linked = [r[0] for r in c.execute(_LINKED_SQL, (workshop_id,)).fetchall()]
        info = {"workshop_id": workshop_id, "name": name[0] if name else workshop_id, "claim_count": count,
                "linked_claim_ids": linked, "linked_count": len(linked)}
        with self._lock:
            self._cache[key] = info
        return info

    def median_amount(self, damage_type: str) -> float:
        key = ("med", damage_type)
        with self._lock:
            if key in self._cache:
                return self._cache[key]
        with self._conn() as c:
            vals = [r[0] for r in c.execute(
                "SELECT amount_claimed FROM claims WHERE damage_type=? AND label='legit' AND source='history'",
                (damage_type,)).fetchall()]
        med = statistics.median(vals) if vals else domain.MEDIAN_AMOUNT.get(damage_type, 1.0)
        with self._lock:
            self._cache[key] = med
        return med

    # ---- sampling for attacker / evaluator / UI
    def sample_claims(self, n: int, rnd: random.Random, *, label="legit", source="history",
                      damage_type=None, workshop=None, not_workshops=()) -> list[Claim]:
        sql, args = "SELECT * FROM claims WHERE label=? AND source=?", [label, source]
        if damage_type:
            sql += " AND damage_type=?"; args.append(damage_type)
        if workshop:
            sql += " AND workshop_id=?"; args.append(workshop)
        for w in not_workshops:
            sql += " AND workshop_id!=?"; args.append(w)
        sql += " ORDER BY claim_id"
        with self._conn() as c:
            rows = c.execute(sql, args).fetchall()
        rows = list(rows)
        rnd.shuffle(rows)
        return [_to_claim(r) for r in rows[:n]]

    def list_samples(self) -> list[dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT claim_id,label,source,workshop_id,damage_type,amount_claimed FROM claims "
                "WHERE source='hero' OR claim_id IN ('CLM-RING-001','CLM-RING-005','CLM-RING-006') "
                "ORDER BY source DESC, claim_id").fetchall()
        return [dict(r) for r in rows]

    def list_claims(self, limit: int = 50, offset: int = 0, query: Optional[str] = None) -> list[dict]:
        with self._conn() as c:
            if query:
                q = f"%{query.strip()}%"
                rows = c.execute(
                    "SELECT claim_id,label,source,workshop_id,damage_type,amount_claimed,incident_date FROM claims "
                    "WHERE claim_id LIKE ? OR workshop_id LIKE ? OR damage_type LIKE ? OR claimant_id LIKE ? "
                    "ORDER BY claim_id LIMIT ? OFFSET ?", (q, q, q, q, limit, offset)).fetchall()
            else:
                rows = c.execute(
                    "SELECT claim_id,label,source,workshop_id,damage_type,amount_claimed,incident_date FROM claims "
                    "ORDER BY claim_id LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        return [dict(r) for r in rows]

    # ---- cases & audit
    def save_case(self, case_id: str, claim_id: str, payload: str) -> None:
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO cases VALUES (?,?,?,?)",
                      (case_id, claim_id, datetime.now(timezone.utc).isoformat(), payload))

    def get_case(self, case_id: str) -> Optional[dict]:
        with self._conn() as c:
            row = c.execute("SELECT payload FROM cases WHERE case_id=?", (case_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def add_audit(self, case_id: str, actor: str, event: str, detail: dict) -> None:
        with self._conn() as c:
            c.execute("INSERT INTO audit_log (case_id,ts,actor,event,detail) VALUES (?,?,?,?,?)",
                      (case_id, datetime.now(timezone.utc).isoformat(), actor, event, json.dumps(detail)))

    def list_workshops(self) -> list[dict]:
        with self._conn() as c:
            rows = c.execute("SELECT workshop_id, name FROM workshops ORDER BY workshop_id").fetchall()
        return [dict(r) for r in rows]

    def add_claim(self, claim: Claim, policy: Optional[dict] = None) -> None:
        with self._conn() as c:
            cols = ["claim_id", "policy_id", "claimant_id", "workshop_id", "bank_account", "phone", "incident_date",
                    "filed_date", "damage_type", "amount_claimed", "narrative", "photo_hash", "photo_caption",
                    "line_items", "source", "label", "photo_url"]
            d = claim.model_dump(mode="json")
            d["line_items"] = json.dumps([it if isinstance(it, dict) else it.model_dump() for it in claim.line_items])
            c.execute(f"INSERT OR REPLACE INTO claims ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                      [d.get(k) for k in cols])
            if policy:
                c.execute("INSERT OR REPLACE INTO policies VALUES (?,?,?,?)",
                          (policy["policy_id"], policy["start_date"], policy["end_date"], policy["coverage_limit"]))
            elif not self.get_policy(claim.policy_id):
                c.execute("INSERT OR REPLACE INTO policies VALUES (?,?,?,?)",
                          (claim.policy_id, "2026-01-01", "2026-12-31", 25000.0))

    def get_audit(self, case_id: str) -> list[dict]:
        with self._conn() as c:
            rows = c.execute("SELECT ts,actor,event,detail FROM audit_log WHERE case_id=? ORDER BY id", (case_id,)).fetchall()
        return [{**dict(r), "detail": json.loads(r["detail"])} for r in rows]
