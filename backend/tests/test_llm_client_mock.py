from app.config import settings
from app.schemas.llm import (
    EvaluationResult,
    ExtractionResult,
    JDParsingResult,
    QuestionPlan,
)
from app.services.llm_client import call_structured, trim_to_budget


def test_trim_to_budget():
    text = "Paragraph 1.\n\nParagraph 2 is longer.\n\nParagraph 3 is the conclusion."
    trimmed = trim_to_budget(text, 35)
    assert len(trimmed) <= 50
    assert "[truncated]" in trimmed


def test_mock_fixtures_load_and_validate():
    # Force mock mode
    orig_mock = settings.LLM_MOCK
    settings.LLM_MOCK = True
    try:
        # JD Parsing
        jd_res = call_structured(
            stage="jd_parsing",
            model="gpt-4o-mini",
            system_prompt="system",
            user_prompt="user",
            schema=JDParsingResult,
        )
        assert isinstance(jd_res, JDParsingResult)
        assert len(jd_res.competencies) >= 4

        # Extraction
        ext_res = call_structured(
            stage="extraction",
            model="gpt-4o-mini",
            system_prompt="system",
            user_prompt="user",
            schema=ExtractionResult,
        )
        assert isinstance(ext_res, ExtractionResult)
        assert len(ext_res.evidence) >= 1

        # Question Plan
        q_res = call_structured(
            stage="question_plan",
            model="gpt-4o",
            system_prompt="system",
            user_prompt="user",
            schema=QuestionPlan,
        )
        assert isinstance(q_res, QuestionPlan)
        assert len(q_res.questions) == 6

        # Evaluation
        eval_res = call_structured(
            stage="evaluation",
            model="gpt-4o",
            system_prompt="system",
            user_prompt="user",
            schema=EvaluationResult,
        )
        assert isinstance(eval_res, EvaluationResult)
        assert len(eval_res.per_question) == 6
    finally:
        settings.LLM_MOCK = orig_mock
