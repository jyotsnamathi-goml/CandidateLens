"""
Deterministic Scoring and Confidence Engine.
Pure functions that calculate 0-100 component scores, redistribute weights for sparse candidates,
assign Readiness Bands, and compute Confidence levels with plain-language explanations.
"""

import hashlib
import json
from typing import Any, Literal

from app.config import settings
from app.schemas.llm import EvaluationResult, EvidenceItem, Flag

DEFAULT_WEIGHTS: dict[str, float] = {
    "jd_alignment": 20.0,
    "technical_depth_evidence": 15.0,
    "ownership_activity": 10.0,
    "practical_problem_solving": 15.0,
    "technical_quality_assessment": 20.0,
    "communication": 5.0,
    "evidence_consistency": 15.0,
}

EVIDENCE_COMPONENTS = {"jd_alignment", "technical_depth_evidence", "ownership_activity"}


def rubric_to_100(val: float | int) -> float:
    """Map 1..5 rubric score to 0..100 scale."""
    clamped = max(1.0, min(5.0, float(val)))
    return round((clamped - 1.0) / 4.0 * 100.0, 1)


def compute_score(
    components: dict[str, float],
    weights: dict[str, float] | None = None,
    sufficiency: str = "sparse",
    sparse_factor: float = 0.5,
) -> tuple[float, dict[str, float]]:
    """
    Compute final weighted readiness score (0-100) and adjusted component weights.
    Redistributes weight from evidence components to assessment components if footprint is sparse.
    """
    w = dict(weights or DEFAULT_WEIGHTS)

    if sufficiency.lower() == "sparse":
        freed = 0.0
        for k in EVIDENCE_COMPONENTS:
            original = w[k]
            new_val = original * sparse_factor
            freed += original - new_val
            w[k] = new_val

        assess = [k for k in w if k not in EVIDENCE_COMPONENTS]
        total_assess = sum(w[k] for k in assess)
        if total_assess > 0:
            for k in assess:
                w[k] += freed * (w[k] / total_assess)

    total_w = sum(w.values())
    if total_w <= 0:
        total_w = 1.0

    score = sum(w[k] * components.get(k, 0.0) for k in w) / total_w
    adjusted_weights = {k: round(v, 2) for k, v in w.items()}
    return round(score, 1), adjusted_weights


def calculate_component_scores(
    relevance_map: dict[str, dict[str, Any]],
    evidence_items: list[EvidenceItem],
    github_metrics: dict[str, Any],
    eval_result: EvaluationResult,
    has_followups: bool = False,
) -> dict[str, float]:
    """Calculate each of the 7 component scores (0 to 100)."""
    # 1. JD Alignment (20%)
    if relevance_map:
        best_scores = [v.get("best_score", 0.0) for v in relevance_map.values()]
        jd_align = (sum(best_scores) / len(best_scores)) * 100.0 if best_scores else 50.0
    else:
        jd_align = 50.0

    # 2. Technical Depth from Evidence (15%)
    if evidence_items:
        weighted_depths = [
            ev.attributes.technical_depth * ev.attributes.evidence_strength
            for ev in evidence_items
        ]
        sum_weights = sum(ev.attributes.evidence_strength for ev in evidence_items) or 1.0
        tech_depth_ev = (sum(weighted_depths) / sum_weights) * 100.0
    else:
        tech_depth_ev = 40.0

    # 3. Ownership and Activity (10%)
    gh_share = github_metrics.get("user_commit_share", 0.8)
    orig_bonus = 1.0 if github_metrics.get("original_repos_count", 0) > 0 else 0.7
    ev_ownership = (
        sum(ev.attributes.ownership for ev in evidence_items) / len(evidence_items)
        if evidence_items
        else 0.6
    )
    ownership_activity = min(100.0, (0.4 * gh_share + 0.3 * orig_bonus + 0.3 * ev_ownership) * 100.0)

    # Assessment turns averaging (weight follow-ups 1.5x depth signal)
    depth_multiplier = 1.05 if has_followups else 1.0

    # 4. Practical Problem Solving (15%)
    ps_scores = [
        rubric_to_100(q.problem_solving.score * 0.6 + q.mechanism.score * 0.4)
        for q in eval_result.per_question
    ]
    problem_solving = min(100.0, (sum(ps_scores) / max(len(ps_scores), 1)) * depth_multiplier)

    # 5. Technical Quality of Assessment (20%)
    tq_scores = [
        rubric_to_100(
            q.technical_correctness.score * 0.4
            + q.technical_depth.score * 0.35
            + q.trade_offs.score * 0.25
        )
        for q in eval_result.per_question
    ]
    technical_quality = min(100.0, (sum(tq_scores) / max(len(tq_scores), 1)) * depth_multiplier)

    # 6. Communication and Answer Quality (5%)
    comm_scores = [rubric_to_100(q.communication.score) for q in eval_result.per_question]
    communication = sum(comm_scores) / max(len(comm_scores), 1)

    # 7. Evidence Consistency / Independent Reasoning (15%)
    consistency_map = {"high": 90.0, "medium": 65.0, "low": 35.0}
    base_cons = consistency_map.get(eval_result.evidence_consistency.lower(), 65.0)

    # Penalties for unresolved flags
    flag_penalty = 0.0
    for fl in eval_result.flags:
        if fl.severity == "high":
            flag_penalty += 15.0
        elif fl.severity == "medium":
            flag_penalty += 8.0

    mean_specificity = (
        sum(rubric_to_100(q.specificity.score) for q in eval_result.per_question)
        / max(len(eval_result.per_question), 1)
    )
    consistency_score = max(0.0, min(100.0, (0.6 * base_cons + 0.4 * mean_specificity) - flag_penalty))

    return {
        "jd_alignment": round(jd_align, 1),
        "technical_depth_evidence": round(tech_depth_ev, 1),
        "ownership_activity": round(ownership_activity, 1),
        "practical_problem_solving": round(problem_solving, 1),
        "technical_quality_assessment": round(technical_quality, 1),
        "communication": round(communication, 1),
        "evidence_consistency": round(consistency_score, 1),
    }


def determine_confidence(
    sufficiency: str,
    critical_assessed: bool,
    flags: list[Flag],
    avg_words: int,
) -> tuple[Literal["High", "Medium", "Low"], str]:
    """Calculate confidence level and plain-language explanation."""
    high_flags = [f for f in flags if f.severity == "high"]
    medium_flags = [f for f in flags if f.severity == "medium"]

    reasons: list[str] = []

    # Sufficiency contribution
    if sufficiency == "rich":
        sufficiency_pts = 3
        reasons.append("public footprint is well-documented")
    elif sufficiency == "partial":
        sufficiency_pts = 2
        reasons.append("public footprint provides moderate evidence")
    else:
        sufficiency_pts = 1
        reasons.append("public footprint is sparse")

    # Assessment depth
    if critical_assessed and avg_words >= 50:
        assess_pts = 3
        reasons.append("practical assessment thoroughly covered all critical competencies")
    elif critical_assessed:
        assess_pts = 2
        reasons.append("assessment covered competencies with concise answers")
    else:
        assess_pts = 1
        reasons.append("some critical competencies had limited direct coverage")

    # Flag consistency
    if not high_flags and len(medium_flags) <= 1:
        flag_pts = 3
    elif len(high_flags) == 1 or len(medium_flags) <= 2:
        flag_pts = 2
        reasons.append("identified minor claim scope gaps for verification")
    else:
        flag_pts = 1
        reasons.append("unresolved evidence mismatches observed")

    total_pts = sufficiency_pts + assess_pts + flag_pts

    if total_pts >= 8:
        conf: Literal["High", "Medium", "Low"] = "High"
    elif total_pts >= 5:
        conf = "Medium"
    else:
        conf = "Low"

    # Rule: Cap at Medium when sufficiency is Sparse unless every critical competency was assessed with consistent, specific answers
    if sufficiency == "sparse" and conf == "High":
        conf = "Medium"

    plain_reason = (
        f"Confidence is {conf} because {'; '.join(reasons)}."
    )
    return conf, plain_reason


def determine_band(
    score: float,
    confidence: str,
    flags: list[Flag],
    all_critical_assessed: bool = True,
    sufficiency: str = "sparse",
) -> Literal["Strong Readiness", "Moderate Readiness", "Needs Verification"]:
    """
    Determine Readiness Band.
    Rule: Sparse evidence alone must NEVER trigger 'Needs Verification'.
    """
    high_flags = [f for f in flags if f.severity == "high"]

    # Needs verification triggers:
    # 1. Score < 60
    # 2. Critical competency completely unassessed
    # 3. Two or more unresolved high-severity flags
    if score < settings.BAND_MODERATE_MIN or (not all_critical_assessed) or len(high_flags) >= 2:
        return "Needs Verification"

    # Strong Readiness:
    # Score >= 80, no high-severity flag, confidence >= Medium
    if score >= settings.BAND_STRONG_MIN and len(high_flags) == 0 and confidence in ["High", "Medium"]:
        return "Strong Readiness"

    # Otherwise Moderate Readiness
    return "Moderate Readiness"


def hash_scoring_inputs(components: dict[str, float], weights: dict[str, float], sufficiency: str) -> str:
    """Create reproducible SHA-256 hash of scoring inputs."""
    data = {
        "components": sorted(components.items()),
        "weights": sorted(weights.items()),
        "sufficiency": sufficiency,
    }
    dumped = json.dumps(data, sort_keys=True)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()
