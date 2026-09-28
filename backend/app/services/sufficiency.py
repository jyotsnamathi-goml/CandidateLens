"""
Evidence Sufficiency evaluation service.
Classifies public and candidate footprint into Rich, Partial, or Sparse.
Identifies uncovered competencies for assessment question generation.
"""

from typing import Any, Literal

from app.schemas.llm import EvidenceItem


def evaluate_sufficiency(
    evidence_items: list[EvidenceItem],
    competencies: list[dict[str, Any]],
    relevance_map: dict[str, dict[str, Any]],
) -> tuple[Literal["rich", "partial", "sparse"], list[str]]:
    """
    Evaluate candidate evidence footprint:
    - Rich: >= 3 items with evidence_strength >= 0.6 AND >= 70% of critical competencies covered (relevance >= 0.5).
    - Partial: >= 1 item with evidence_strength >= 0.5 AND 30% to 70% of critical competencies covered.
    - Sparse: otherwise.
    Returns (sufficiency, uncovered_competencies).
    """
    critical_comps = [
        c.get("name", "")
        for c in competencies
        if c.get("importance") == "critical" or c.get("rank", 99) <= 2
    ]
    if not critical_comps:
        critical_comps = [c.get("name", "") for c in competencies[:3]]

    strong_items = [ev for ev in evidence_items if ev.attributes.evidence_strength >= 0.6]
    moderate_items = [ev for ev in evidence_items if ev.attributes.evidence_strength >= 0.5]

    covered_critical = 0
    uncovered_competencies: list[str] = []

    for comp in competencies:
        name = comp.get("name", "")
        rel_info = relevance_map.get(name, {})
        best_score = rel_info.get("best_score", 0.0)

        if best_score >= 0.5:
            if name in critical_comps:
                covered_critical += 1
        else:
            uncovered_competencies.append(name)

    critical_total = max(len(critical_comps), 1)
    coverage_ratio = covered_critical / critical_total

    if len(strong_items) >= 3 and coverage_ratio >= 0.70:
        sufficiency: Literal["rich", "partial", "sparse"] = "rich"
    elif len(moderate_items) >= 1 and coverage_ratio >= 0.30:
        sufficiency = "partial"
    else:
        sufficiency = "sparse"

    return sufficiency, uncovered_competencies
