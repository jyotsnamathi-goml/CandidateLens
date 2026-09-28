"""
Question Generation Service (LLM Call 2).
Designs a 6-question practical assessment tailored to JD competencies and candidate claims.
Includes fallback template question bank if generation fails.
"""

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.schemas.llm import PlannedQuestion, QuestionPlan
from app.services.llm_client import call_structured, trim_to_budget
from app.services.prompts import QUESTION_PLAN_SYSTEM_PROMPT

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def get_fallback_question_plan(competencies: list[dict[str, Any]], role_family: str) -> QuestionPlan:
    """Load deterministic fallback question bank when Call 2 fails or is unavailable."""
    fb_path = FIXTURES_DIR / "fallback_questions.json"
    data = {}
    if fb_path.exists():
        with open(fb_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    family_key = role_family if role_family in data else "backend"
    raw_questions = data.get(family_key, data.get("backend", []))

    comp_names = [c.get("name", f"Competency {i+1}") for i, c in enumerate(competencies)]
    while len(comp_names) < 4:
        comp_names.append(f"Technical Area {len(comp_names)+1}")

    formatted_questions: list[PlannedQuestion] = []
    for i, q in enumerate(raw_questions[:6]):
        comp_idx = i % len(comp_names)
        text = q["text"].replace("{competency_1}", comp_names[0])
        text = text.replace("{competency_2}", comp_names[1 % len(comp_names)])
        text = text.replace("{competency_3}", comp_names[2 % len(comp_names)])
        text = text.replace("{competency_4}", comp_names[3 % len(comp_names)])

        formatted_questions.append(
            PlannedQuestion(
                question_id=f"q{i+1}",
                kind=q.get("kind", "jd_scenario"),
                competency=comp_names[comp_idx],
                evidence_refs=q.get("evidence_refs", []),
                text=text,
                what_good_looks_like=q.get("what_good_looks_like", []),
                follow_up_if_vague=q.get("follow_up_if_vague", "Could you provide more specific implementation details?"),
                follow_up_if_strong=q.get("follow_up_if_strong"),
            )
        )

    return QuestionPlan(questions=formatted_questions)


def generate_question_plan(
    candidate_id: str,
    role_title: str,
    role_family: str,
    competencies: list[dict[str, Any]],
    uncovered_competencies: list[str],
    evidence_items: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    sufficiency: str,
    db: Session | None = None,
) -> QuestionPlan:
    """Generate 6-question assessment plan using LLM Call 2 with fallback."""
    # Build prompt payload
    condensed_evidence = [
        {
            "id": ev.get("evidence_id"),
            "title": ev.get("title"),
            "tech": ev.get("technologies", [])[:5],
            "role": ev.get("role"),
            "strength": ev.get("attributes", {}).get("evidence_strength", 0.5),
        }
        for ev in evidence_items[:6]
    ]

    condensed_claims = [
        {"id": cl.get("claim_id"), "text": cl.get("text"), "scope": cl.get("scope")}
        for cl in claims[:8]
    ]

    user_prompt = f"""Role: {role_title} (Family: {role_family})
Sufficiency: {sufficiency}

Competencies:
{json.dumps(competencies, indent=2)}

Uncovered Competencies (Priority for q1-q4):
{json.dumps(uncovered_competencies, indent=2)}

Condensed Evidence Items:
{json.dumps(condensed_evidence, indent=2)}

Candidate Claims to probe (for q5-q6):
{json.dumps(condensed_claims, indent=2)}

Create exactly 6 questions (q1-q4 JD scenarios, q5-q6 candidate project/verification questions).
Return ONLY JSON matching the schema.
"""
    trimmed_prompt = trim_to_budget(user_prompt, settings.MAX_INPUT_CHARS_QUESTIONS)

    try:
        plan: QuestionPlan = call_structured(
            stage="question_plan",
            model=settings.OPENAI_MODEL_STRONG,
            system_prompt=QUESTION_PLAN_SYSTEM_PROMPT,
            user_prompt=trimmed_prompt,
            schema=QuestionPlan,
            candidate_id=candidate_id,
            temperature=settings.LLM_TEMPERATURE_QUESTIONS,
            max_output_tokens=settings.MAX_OUTPUT_TOKENS_QUESTIONS,
            is_essential=True,
            db=db,
        )
        return plan
    except Exception:
        # Fall back to template question bank
        return get_fallback_question_plan(competencies, role_family)
