"""
Relevance service: calculates alignment between JD competencies and extracted evidence.
Uses normalized keyword overlap + TF-IDF-inspired weighting, blended with LLM jd_relevance.
"""

import math
from typing import Any

from app.schemas.llm import EvidenceItem


def tokenize(text: str) -> set[str]:
    """Basic tokenizer converting to lower-case alphanumeric word set."""
    import re
    return set(re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text.lower()))


def calculate_keyword_overlap(competency: str, evidence: EvidenceItem) -> float:
    """Compute normalized token overlap between competency description and evidence text."""
    comp_tokens = tokenize(competency)
    if not comp_tokens:
        return 0.0

    ev_text = f"{evidence.title} {' '.join(evidence.technologies)} {' '.join(evidence.responsibilities)} {' '.join(evidence.outcomes)}"
    ev_tokens = tokenize(ev_text)

    overlap = len(comp_tokens.intersection(ev_tokens))
    # Normalized score with dampening
    raw_score = overlap / math.sqrt(len(comp_tokens) + 1)
    return min(1.0, raw_score)


def match_evidence_to_competencies(
    competencies: list[dict[str, Any]],
    evidence_items: list[EvidenceItem],
) -> dict[str, dict[str, Any]]:
    """
    For each competency, compute relevance across all evidence items.
    Returns mapping:
    {
      competency_name: {
         "best_evidence_id": "ev_001",
         "best_score": 0.85,
         "all_scores": {"ev_001": 0.85, ...}
      }
    }
    """
    results: dict[str, dict[str, Any]] = {}

    for comp in competencies:
        comp_name = comp.get("name", "")
        comp_desc = comp.get("description", "")
        combined_comp = f"{comp_name} {comp_desc}"

        best_score = 0.0
        best_ev_id: str | None = None
        ev_scores: dict[str, float] = {}

        for ev in evidence_items:
            # 1. Deterministic keyword overlap (50% weight)
            kw_overlap = calculate_keyword_overlap(combined_comp, ev)
            # 2. LLM perceived jd_relevance (50% weight)
            llm_rel = ev.attributes.jd_relevance

            blended = round(0.4 * kw_overlap + 0.6 * llm_rel, 3)
            ev_scores[ev.evidence_id] = blended

            if blended > best_score:
                best_score = blended
                best_ev_id = ev.evidence_id

        results[comp_name] = {
            "best_evidence_id": best_ev_id,
            "best_score": best_score,
            "all_scores": ev_scores,
        }

    return results
