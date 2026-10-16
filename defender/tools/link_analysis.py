"""Tool: find hidden links between a claim and the claim history."""
from shared.schemas import GraphEdge, GraphNode, Signal

CLUSTER_MIN_LINKED = 4
CLUSTER_MIN_DENSITY = 0.15


def find_links(repo, claim) -> dict:
    return {
        "account": repo.claims_sharing("bank_account", claim.bank_account, claim.claim_id),
        "phone": repo.claims_sharing("phone", claim.phone, claim.claim_id),
        "photo": repo.claims_sharing("photo_hash", claim.photo_hash, claim.claim_id),
        "duplicate": repo.same_claimant_same_type(claim.claimant_id, claim.damage_type, claim.claim_id),
        "workshop": repo.workshop_info(claim.workshop_id),
    }


def link_signals(claim, links: dict) -> tuple[list[Signal], str]:
    sigs: list[Signal] = []
    ids = lambda rows: [r["claim_id"] for r in rows]
    n = len(links["account"])
    if n >= 2:
        sigs.append(Signal(type="shared_bank_account", severity="high", weight=25,
                           evidence=f"Payout account {claim.bank_account} appears in {n} other claims.", claim_ids=ids(links["account"])))
    elif n == 1:
        sigs.append(Signal(type="shared_bank_account", severity="low", weight=5,
                           evidence=f"Payout account {claim.bank_account} appears in 1 other claim.", claim_ids=ids(links["account"])))
    n = len(links["phone"])
    if n >= 2:
        sigs.append(Signal(type="shared_phone", severity="medium", weight=15,
                           evidence=f"Phone {claim.phone} appears in {n} other claims.", claim_ids=ids(links["phone"])))
    elif n == 1:
        sigs.append(Signal(type="shared_phone", severity="low", weight=3,
                           evidence=f"Phone {claim.phone} appears in 1 other claim.", claim_ids=ids(links["phone"])))
    if links["photo"]:
        sigs.append(Signal(type="reused_photo", severity="high", weight=25,
                           evidence=f"The damage photo is identical to photos in {len(links['photo'])} other claim(s).", claim_ids=ids(links["photo"])))
    if links["duplicate"]:
        sigs.append(Signal(type="near_duplicate", severity="medium", weight=20,
                           evidence=f"The same claimant already filed a {claim.damage_type} claim ({links['duplicate'][0]['claim_id']}).", claim_ids=ids(links["duplicate"])))
    ws = links["workshop"]
    density = ws["linked_count"] / ws["claim_count"] if ws["claim_count"] else 0.0
    if ws["linked_count"] >= CLUSTER_MIN_LINKED and density >= CLUSTER_MIN_DENSITY:
        sigs.append(Signal(type="workshop_cluster", severity="high", weight=20,
                           evidence=f"{ws['name']} ({ws['workshop_id']}): {ws['linked_count']} of {ws['claim_count']} claims share payout accounts, phones or photos with each other.",
                           claim_ids=ws["linked_claim_ids"][:12]))
        note = f"{ws['name']} shows a tight cluster ({density:.0%} of its claims are interlinked), well above normal."
    else:
        note = (f"{ws['name']} handles {ws['claim_count']} claims; {ws['linked_count']} of them share payout accounts, phones or photos "
                f"with each other ({density:.0%}). Volume alone is not suspicious.")
    return sigs, note


def build_graph(claim, links: dict) -> tuple[list[GraphNode], list[GraphEdge]]:
    nodes = {claim.claim_id: GraphNode(id=claim.claim_id, kind="claim_focus", label=claim.claim_id)}
    edges: list[GraphEdge] = []

    def entity(kind: str, value: str, rows: list[dict]) -> None:
        eid = f"{kind}:{value}"
        nodes[eid] = GraphNode(id=eid, kind=kind, label=value)
        edges.append(GraphEdge(source=claim.claim_id, target=eid, relation=kind))
        for r in rows[:12]:
            nodes.setdefault(r["claim_id"], GraphNode(id=r["claim_id"], kind="claim_linked", label=r["claim_id"]))
            edges.append(GraphEdge(source=eid, target=r["claim_id"], relation="used_in"))

    if links["account"]:
        entity("bank_account", claim.bank_account, links["account"])
    if links["phone"]:
        entity("phone", claim.phone, links["phone"])
    if links["photo"]:
        entity("photo", claim.photo_hash, links["photo"])
    ws = links["workshop"]
    if ws["linked_count"] >= CLUSTER_MIN_LINKED and ws["linked_count"] / max(ws["claim_count"], 1) >= CLUSTER_MIN_DENSITY:
        entity("workshop", ws["name"], [{"claim_id": c} for c in ws["linked_claim_ids"] if c != claim.claim_id])
    return list(nodes.values()), edges
