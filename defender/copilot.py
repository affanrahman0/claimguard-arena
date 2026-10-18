"""SIU Interrogation Copilot: Generates targeted cross-examination questions and evaluates claimant responses."""
import json
from typing import Optional
from pydantic import BaseModel, Field

from shared import config, domain, llm
from shared.schemas import CaseResult


class CopilotQuestionItem(BaseModel):
    id: str
    target_signal: str
    question: str
    objective: str
    suggested_answers: list[str] = Field(default_factory=list)


class CopilotQuestionsPayload(BaseModel):
    questions: list[CopilotQuestionItem]


class CopilotEvaluation(BaseModel):
    plausibility_score: int
    credibility_assessment: str
    deception_markers: list[str] = Field(default_factory=list)
    recommended_siu_action: str


def _mock_questions(case: CaseResult) -> CopilotQuestionsPayload:
    c = case.claim
    p = case.policy
    f = case.fraud
    sig_types = {s.type for s in p.signals + f.signals}
    items = []

    # 1. Directional / Narrative Mismatch
    if "narrative_estimate_mismatch" in sig_types or "side" in c.narrative.lower() or "rear" in c.narrative.lower():
        items.append(CopilotQuestionItem(
            id="Q1",
            target_signal="Spatial & Directional Damage Contradiction",
            question=f"You stated in your written statement: '{c.narrative}', yet repair line items and garage photographs document primary structural impact to the {c.photo_caption or 'front impact zone'}. Can you explain what specific force caused damage to parts completely opposite to your stated impact direction?",
            objective="Compel claimant to reconcile directional physics before presenting cryptographic photo evidence.",
            suggested_answers=[
                "Claimant states: 'There was a secondary spin-out after the initial contact that tapped another barrier.'",
                "Claimant evades: 'I was disoriented after the airbag deployed; the repair garage drafted the description.'",
                "Claimant contradicts: 'Actually, the car might have had a small previous bump in the parking lot.'"
            ]
        ))
    else:
        items.append(CopilotQuestionItem(
            id="Q1",
            target_signal="Incident Sequence & Timeline Verification",
            question=f"On {c.incident_date}, you reported an incident resulting in ${c.amount_claimed:,.2f} of vehicle damage. Who was operating the vehicle at the exact moment of loss, and were there any third-party witnesses or dashcam recordings?",
            objective="Establish sworn driver identity, exact timeline, and external corroboration availability.",
            suggested_answers=[
                "Claimant claims: 'I was driving alone at night on a dark suburban stretch; no witnesses stopped.'",
                "Claimant mentions witness: 'A passerby stopped briefly but did not leave contact details.'",
                "Claimant hesitates: 'A friend was test-driving my car, but I am the registered policyholder.'"
            ]
        ))

    # 2. Image Reuse / Invoice Tampering / Arithmetic Spikes
    if any(s in sig_types for s in ("reused_photo", "cluster_photo")):
        items.append(CopilotQuestionItem(
            id="Q2",
            target_signal="Perceptual Photo Checksum Duplication",
            question=f"Our digital forensics engine identified that the damage photo hash ({c.photo_hash[:12]}...) submitted with this claim is identical to an image filed on a prior claim. Did you take this photograph with your mobile device on the date of loss, or did the repair facility supply it?",
            objective="Pin responsibility for recycled photographic evidence directly to claimant or workshop.",
            suggested_answers=[
                "Claimant blames workshop: 'The service manager at the garage said he would take and upload all damage photos.'",
                "Claimant stumbles: 'I may have accidentally uploaded an older photo saved in my cloud camera roll.'",
                "Claimant becomes defensive: 'I don't know anything about hashes; that is my car and you need to pay.'"
            ]
        ))
    elif "sum_mismatch" in sig_types:
        lines_sum = sum(i.amount for i in c.line_items)
        items.append(CopilotQuestionItem(
            id="Q2",
            target_signal="Invoice Arithmetic Inflation & Tampering",
            question=f"The itemized parts and labor lines submitted from workshop {c.workshop_id} sum to ${lines_sum:,.2f}, yet your official claim request totals ${c.amount_claimed:,.2f} (a discrepancy of ${abs(c.amount_claimed - lines_sum):,.2f}). Who adjusted this bottom-line payout amount?",
            objective="Probe whether claimant or garage deliberately altered total payout requested.",
            suggested_answers=[
                "Claimant states: 'The garage added expedited parts freight and diagnostic fees not itemized.'",
                "Claimant deflects: 'I entered what was written on the summary header slip; I didn't add up the rows.'",
                "Claimant concedes: 'If there is an error in the addition, please pay the actual itemized total.'"
            ]
        ))
    else:
        items.append(CopilotQuestionItem(
            id="Q2",
            target_signal="Repair Invoice & Market Rate Assessment",
            question=f"The repair estimate of ${c.amount_claimed:,.2f} for {c.damage_type} at workshop {c.workshop_id} exceeds regional benchmark distributions. Did you obtain a competing quote, and did the garage offer to waive your deductible?",
            objective="Detect potential estimate padding or garage-claimant rebate kickback arrangements.",
            suggested_answers=[
                "Claimant denies: 'No, this was the closest garage after the breakdown and their quote felt normal.'",
                "Claimant admits discount: 'The shop manager said he could work with my deductible if insurance cleared it.'",
                "Claimant neutral: 'I simply authorized whatever repairs the certified technician deemed necessary.'"
            ]
        ))

    # 3. Policy Clauses / Syndicate / Bank Link
    if p.excluded:
        items.append(CopilotQuestionItem(
            id="Q3",
            target_signal="Clause 4.1 Statutory Wear & Tear Exclusion",
            question=f"Policy Clause 4.1 strictly excludes gradual mechanical breakdown, rust, and normal tire/brake pad wear. Can you provide evidence of a sudden external accidental force causing this degradation?",
            objective="Differentiate sudden insurable peril from routine non-covered maintenance overhead.",
            suggested_answers=[
                "Claimant claims suddenness: 'It was working fine until I drove over debris on the highway, then it failed.'",
                "Claimant concedes wear: 'The mechanic mentioned it was getting worn, but said I could claim it after the bump.'",
                "Claimant appeals: 'I have paid premiums for 3 years without a claim and expected full coverage.'"
            ]
        ))
    elif any(s in sig_types for s in ("cluster_bank", "cluster_phone", "syndicate_link")):
        items.append(CopilotQuestionItem(
            id="Q3",
            target_signal="Shared Payout Entity & Ring Association",
            question=f"Your claim specifies settlement to bank account {c.bank_account}, which is linked in underwriting records to multiple prior claims originating from workshop {c.workshop_id}. What is your legal relationship to this payee account?",
            objective="Establish intentional entity sharing in syndicated staged-accident schemes.",
            suggested_answers=[
                "Claimant explains family link: 'That account belongs to my brother-in-law who loaned me money for repairs.'",
                "Claimant claims garage instructed: 'The shop instructed me to route insurance proceeds directly to their vendor account.'",
                "Claimant denies knowledge: 'I provided my personal checking details; I have no idea why another number appears.'"
            ]
        ))
    else:
        items.append(CopilotQuestionItem(
            id="Q3",
            target_signal="Pre-Existing Damage & Prior Loss Disclosure",
            question="Has this vehicle sustained any prior accidents, body panel repairs, or windshield replacements in the 12 months preceding this loss that were not reported to ClaimGuard Mutual?",
            objective="Verify pre-existing condition warranties and prevent double-recovery indemnification.",
            suggested_answers=[
                "Claimant affirms clean history: 'The vehicle was in pristine condition with zero prior damage or claims.'",
                "Claimant acknowledges minor event: 'A small door ding occurred last year in a parking lot, but nothing structural.'",
                "Claimant uncertain: 'I purchased the vehicle second-hand six months ago and cannot speak to prior history.'"
            ]
        ))

    return CopilotQuestionsPayload(questions=items[:3])


def generate_questions(case: CaseResult) -> tuple[CopilotQuestionsPayload, str]:
    c = case.claim
    p = case.policy
    f = case.fraud
    items_str = "\n".join(f"- {it.description}: ${it.amount:,.2f}" for it in c.line_items)
    signals_str = ", ".join(s.type for s in p.signals + f.signals) or "None (Clean Claim)"
    
    prompt = (
        f"You are a Senior Insurance Fraud Investigator (SIU) preparing to cross-examine a motor insurance claimant.\n"
        f"Generate exactly 3 sharp, forensic, legally precise cross-examination questions to probe inconsistencies in this claim.\n\n"
        f"Claim Information:\n"
        f"- Claim ID: {c.claim_id}\n"
        f"- Damage Type: {c.damage_type}\n"
        f"- Amount Claimed: ${c.amount_claimed:,.2f}\n"
        f"- Narrative Statement: \"{c.narrative}\"\n"
        f"- Photo Caption / Inspection: \"{c.photo_caption}\" (MD5: {c.photo_hash})\n"
        f"- Workshop: {c.workshop_id}\n"
        f"- Repair Invoice Lines:\n{items_str}\n"
        f"- Policy Terms: Excluded={p.excluded}, In-Period={p.in_period}, Within-Limit={p.within_limit}\n"
        f"- Detected Signals: {signals_str}\n"
        f"- Decision Risk Score: {case.decision.risk_score}/100 ({case.decision.recommendation})\n\n"
        f"For each of the 3 questions, provide:\n"
        f"- id: 'Q1', 'Q2', or 'Q3'\n"
        f"- target_signal: Short headline of the discrepancy probed\n"
        f"- question: Verbatim cross-examination question to ask the claimant\n"
        f"- objective: Investigative tactical objective\n"
        f"- suggested_answers: List of 2 to 3 realistic sample responses (evasive, contradictory, defensive)"
    )

    return llm.generate_json(
        prompt,
        CopilotQuestionsPayload,
        lambda: _mock_questions(case),
        system="You are an expert SIU interrogator and insurance legal counsel. Be sharp, factual, and precise.",
        model=config.MODEL_FAST,
        temperature=0.2,
    )


def _mock_evaluate(case: CaseResult, question: str, claimant_answer: str) -> CopilotEvaluation:
    ans_lower = claimant_answer.lower()
    score = 65
    deceptions = []
    action = "Request Supporting In-Person Vehicle Inspection"

    if any(w in ans_lower for w in ("garage", "mechanic", "shop", "manager")):
        deceptions.append("Agency deflection to third-party repair facility")
        score -= 20
    if any(w in ans_lower for w in ("spin-out", "another", "previous", "earlier", "small bump", "before")):
        deceptions.append("Post-hoc narrative revision introducing unverified secondary impact")
        score -= 25
    if any(w in ans_lower for w in ("attorney", "lawyer", "demand", "don't know", "no idea")):
        deceptions.append("Defensive stone-walling / evasive non-response")
        score -= 30
    if any(w in ans_lower for w in ("accidentally", "old photo", "cloud", "gallery")):
        deceptions.append("Admission of photographic evidence substitution")
        score = 15

    score = max(min(score, 90), 10)
    if score < 30:
        action = "Issue Formal Statutory Fraud Denial Notice under Clause 8.4"
    elif score < 60:
        action = "Subpoena Traffic Intersection Footage & Require Sworn Examination Under Oath (EUO)"
    else:
        action = "Approve Claim with Verified Original Parts Receipts Requirement"

    return CopilotEvaluation(
        plausibility_score=score,
        credibility_assessment=(
            f"Claimant explanation ('{claimant_answer[:100]}...') fails to resolve underlying physical and documentary discrepancies. "
            f"The response relies on deflection and lacks contemporaneous corroboration."
            if score < 50 else
            f"Claimant provided a contextually plausible clarification, though physical inspection is recommended to verify consistency."
        ),
        deception_markers=deceptions or ["Lack of independent third-party corroboration"],
        recommended_siu_action=action,
    )


def evaluate_statement(case: CaseResult, question: str, claimant_answer: str) -> tuple[CopilotEvaluation, str]:
    c = case.claim
    prompt = (
        f"You are a Forensic SIU Claims Adjudicator and credibility analyst.\n"
        f"Evaluate the claimant's sworn answer against the forensic evidence of this motor insurance claim.\n\n"
        f"Context:\n"
        f"- Claim: {c.claim_id} (${c.amount_claimed:,.2f}, {c.damage_type})\n"
        f"- Written Narrative: \"{c.narrative}\"\n"
        f"- Evidence Photo: \"{c.photo_caption}\" (Hash: {c.photo_hash})\n"
        f"- Interrogator Question: \"{question}\"\n"
        f"- Claimant Answer: \"{claimant_answer}\"\n\n"
        f"Analyze the explanation for physical plausibility, evasiveness, agency deflection, and timeline consistency.\n"
        f"Return JSON:\n"
        f"- plausibility_score: integer 0-100 (0=completely fraudulent/implausible, 100=fully genuine)\n"
        f"- credibility_assessment: 2-3 sentence rigorous forensic adjudication\n"
        f"- deception_markers: array of 2-4 detected deception traits (e.g. 'Deflection of agency to workshop', 'Unverifiable secondary impact assertion', 'Temporal shifting')\n"
        f"- recommended_siu_action: clear actionable SIU next step (e.g. 'Refer for Formal Fraud Denial (Clause 8.4)', 'Demand Sworn Examination Under Oath (EUO)', 'Clear Payout with Secondary Verification')"
    )

    return llm.generate_json(
        prompt,
        CopilotEvaluation,
        lambda: _mock_evaluate(case, question, claimant_answer),
        system="You are an uncompromising, evidence-based insurance fraud adjudicator.",
        model=config.MODEL_FAST,
        temperature=0.1,
    )
