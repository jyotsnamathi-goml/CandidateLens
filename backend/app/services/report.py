"""
Report Assembly Service (Deterministic, No LLM call).
Assembles the complete Candidate Readiness Signal report from validated evaluation data,
scoring engine components, and stored evidence.
"""

from datetime import datetime, timezone
from typing import Any

from app.schemas.domain import ReadinessReport, ScoreBreakdownItem, TimelineObservation
from app.schemas.llm import EvaluationResult, EvidenceItem

COMPONENT_LABELS = {
    "jd_alignment": ("JD Alignment", "Relevance overlap across critical competencies"),
    "technical_depth_evidence": ("Technical Depth from Evidence", "Engineering complexity of verified artifacts"),
    "ownership_activity": ("Ownership & Activity", "Commit share, original contributions, and repository ownership"),
    "practical_problem_solving": ("Practical Problem Solving", "Root-cause debugging, failure analysis, and mechanics"),
    "technical_quality_assessment": ("Technical Quality of Assessment", "Accuracy, depth, and trade-off considerations in answers"),
    "communication": ("Communication Quality", "Structured reasoning and clarity"),
    "evidence_consistency": ("Evidence Consistency", "Alignment between candidate claims and assessment specificity"),
}


def build_readiness_report(
    candidate_id: str,
    role_id: str,
    role_title: str,
    display_name: str,
    band: str,
    confidence: str,
    confidence_reason: str,
    score: float,
    components: dict[str, float],
    adjusted_weights: dict[str, float],
    sufficiency: str,
    eval_result: EvaluationResult,
    evidence_items: list[EvidenceItem],
    timeline_obs: list[TimelineObservation],
    notes: list[dict[str, Any]] | None = None,
) -> ReadinessReport:
    """Assemble final structured ReadinessReport."""

    breakdown_items: list[ScoreBreakdownItem] = []
    for key, (label, src_desc) in COMPONENT_LABELS.items():
        comp_score = components.get(key, 0.0)
        weight = adjusted_weights.get(key, 0.0)
        weighted_score = round((comp_score * weight) / 100.0, 2)

        breakdown_items.append(
            ScoreBreakdownItem(
                name=key,
                label=label,
                weight=weight,
                score=comp_score,
                weighted_score=weighted_score,
                inputs={"raw_score": comp_score, "assigned_weight": weight},
                source_description=src_desc,
            )
        )

    if sufficiency == "sparse":
        sufficiency_impact = (
            "Because public footprint was sparse, evidence weights were reduced by 50% "
            "and redistributed to the practical assessment. Sparse evidence never by itself lowers the readiness band."
        )
    elif sufficiency == "partial":
        sufficiency_impact = "Public footprint provided moderate signals across key competencies."
    else:
        sufficiency_impact = "Public footprint was rich and corroborated several primary competencies."

    report = ReadinessReport(
        candidate_id=candidate_id,
        role_id=role_id,
        role_title=role_title,
        display_name=display_name,
        band=band,
        confidence=confidence,
        confidence_reason=confidence_reason,
        score=score,
        disclaimer="Candidate Readiness Signal, not a hiring decision.",
        component_breakdown=breakdown_items,
        sufficiency=sufficiency,
        sufficiency_impact=sufficiency_impact,
        strengths=eval_result.strengths,
        verification_points=eval_result.verification_points,
        flags=eval_result.flags,
        timeline_observations=timeline_obs,
        evidence_items=evidence_items,
        assessment_analysis=eval_result.per_question,
        interview_probes=eval_result.interview_probes,
        notes=notes or [],
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    return report
