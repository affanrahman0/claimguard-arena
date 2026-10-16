"""All data contracts. Attacker, defender and evaluator talk to each other only through these."""
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str
    amount: float


class Claim(BaseModel):
    claim_id: str
    policy_id: str
    claimant_id: str
    workshop_id: str
    bank_account: str
    phone: str
    incident_date: date
    filed_date: date
    damage_type: str
    amount_claimed: float
    narrative: str
    photo_hash: str
    photo_caption: str
    line_items: list[LineItem]
    source: str = "history"   # history | hero | adversary
    label: str = "legit"      # legit | ring | policy_violation | attack:<type>
    photo_url: Optional[str] = None


# ---------- Defender outputs ----------
class Signal(BaseModel):
    type: str
    severity: str          # low | medium | high
    weight: int
    evidence: str
    claim_ids: list[str] = Field(default_factory=list)


class PolicyResult(BaseModel):
    covered: bool
    in_period: bool
    excluded: bool
    within_limit: bool
    citations: list[str]
    explanation: str
    signals: list[Signal] = Field(default_factory=list)


class ConsistencyFinding(BaseModel):
    """Also used as the Gemini response schema, so keep it simple."""
    consistent: bool
    issues: list[str]
    confidence: float


class GraphNode(BaseModel):
    id: str
    kind: str
    label: str


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str


class FraudResult(BaseModel):
    signals: list[Signal]
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    consistency: ConsistencyFinding
    baseline_note: str


class Decision(BaseModel):
    risk_score: int
    recommendation: str    # fast_track | investigate | escalate
    reasoning: str
    evidence: list[str]


class AgentEvent(BaseModel):
    agent: str
    status: str = "done"
    summary: str
    detail: dict = Field(default_factory=dict)
    ms: int = 0


class CaseResult(BaseModel):
    case_id: str
    claim: Claim
    events: list[AgentEvent]
    policy: PolicyResult
    fraud: FraudResult
    decision: Decision
    llm_mode: str


# ---------- Attacker output ----------
class AttackCase(BaseModel):
    claim: Claim
    attack_type: str
    stealth: bool
    intent: str


# ---------- Small schemas used as Gemini response formats ----------
class ReasoningOut(BaseModel):
    reasoning: str


class AttackNarrative(BaseModel):
    narrative: str


class Improvement(BaseModel):
    suggestion: str


class ExtractedFields(BaseModel):
    policy_id: str
    incident_date: str
    amount_claimed: float
    damage_type: str
    workshop_id: str
    bank_account: str
    phone: str
    narrative: str
