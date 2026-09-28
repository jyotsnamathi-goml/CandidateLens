"""
Extraction Service (LLM Call 1).
Extracts structured evidence items, claims, and competency coverage from untrusted candidate sources.
Uses the small model (gpt-4o-mini) and strict schema validation.
"""

import json
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.schemas.llm import ExtractionResult
from app.services.llm_client import call_structured, trim_to_budget
from app.services.prompts import EXTRACTION_SYSTEM_PROMPT


def run_extraction(
    candidate_id: str,
    competencies: list[dict[str, Any]],
    resume_text: str,
    github_data: dict[str, Any],
    portfolio_text: str,
    db: Session | None = None,
) -> ExtractionResult:
    """Execute LLM Call 1 to extract structured evidence and claims."""
    # Format and trim input
    trimmed_resume = trim_to_budget(resume_text, 12000)
    trimmed_portfolio = trim_to_budget(portfolio_text, 4000)

    # Clean GitHub data for prompt
    gh_summary = {
        "username": github_data.get("username"),
        "repos": [
            {
                "name": r.get("name"),
                "desc": r.get("description"),
                "lang": r.get("language"),
                "fork": r.get("fork"),
                "stars": r.get("stars"),
                "readme_sample": (r.get("readme_excerpt") or "")[:800],
            }
            for r in github_data.get("top_repos", [])
        ],
        "user_commit_share": github_data.get("user_commit_share"),
        "last_commit_date": github_data.get("last_commit_date"),
    }
    gh_json = json.dumps(gh_summary)
    trimmed_gh = trim_to_budget(gh_json, 6000)

    comp_summary = [
        {"name": c.get("name"), "description": c.get("description"), "rank": c.get("rank")}
        for c in competencies
    ]

    user_prompt = f"""<jd_competencies>
{json.dumps(comp_summary, indent=2)}
</jd_competencies>

<resume>
{trimmed_resume}
</resume>

<github>
{trimmed_gh}
</github>

<portfolio>
{trimmed_portfolio}
</portfolio>

Extract evidence items (max 8) and candidate claims (max 12), and evaluate competency coverage.
Return ONLY valid JSON matching the schema.
"""

    result: ExtractionResult = call_structured(
        stage="extraction",
        model=settings.OPENAI_MODEL_SMALL,
        system_prompt=EXTRACTION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=ExtractionResult,
        candidate_id=candidate_id,
        temperature=settings.LLM_TEMPERATURE_EXTRACT,
        max_output_tokens=settings.MAX_OUTPUT_TOKENS_EXTRACTION,
        is_essential=True,
        db=db,
    )

    return result
