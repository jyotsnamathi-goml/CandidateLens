from app.schemas.llm import (
    DimensionScore,
    EvaluationResult,
    Finding,
    Flag,
    QuestionEvaluation,
)
from app.services.validators import (
    sanitize_forbidden_language,
    validate_grounding,
    validate_quotes,
)


def test_forbidden_language_sanitization():
    accusatory_text = "The candidate is dishonest and lied about their fake project to cheat the review."
    sanitized = sanitize_forbidden_language(accusatory_text)

    assert "dishonest" not in sanitized.lower()
    assert "lied" not in sanitized.lower()
    assert "fake" not in sanitized.lower()
    assert "cheat" not in sanitized.lower()
    assert "unverified" in sanitized or "scope" in sanitized or "divergent" in sanitized


def test_quote_validator_caps_at_two():
    answers = "We used Redis Redlock for distributed locking and PostgreSQL for data storage."

    # Question eval with valid quote
    q_valid = QuestionEvaluation(
        question_id="q1",
        technical_correctness=DimensionScore(score=4, quote="Redis Redlock for distributed locking"),
        technical_depth=DimensionScore(score=3, quote="PostgreSQL for data storage"),
        mechanism=DimensionScore(score=2, quote="general concept"),
        trade_offs=DimensionScore(score=1, quote="none"),
        problem_solving=DimensionScore(score=2, quote=""),
        communication=DimensionScore(score=4, quote="Redis Redlock for distributed locking"),
        specificity=DimensionScore(score=2, quote=""),
    )

    # Question eval with hallucinated quote
    q_invalid = QuestionEvaluation(
        question_id="q2",
        technical_correctness=DimensionScore(score=5, quote="completely made up quote about Kafka"),
        technical_depth=DimensionScore(score=4, quote="another hallucinated sentence"),
        mechanism=DimensionScore(score=2, quote=""),
        trade_offs=DimensionScore(score=1, quote=""),
        problem_solving=DimensionScore(score=2, quote=""),
        communication=DimensionScore(score=2, quote=""),
        specificity=DimensionScore(score=2, quote=""),
    )

    results = validate_quotes([q_valid, q_invalid], answers)

    # q_valid scores should remain 4 and 3
    assert results[0].technical_correctness.score == 4
    assert results[0].technical_depth.score == 3

    # q_invalid scores should be capped at 2
    assert results[1].technical_correctness.score == 2
    assert results[1].technical_depth.score == 2


def test_grounding_validator_drops_invalid_refs():
    all_answers = "I implemented Redlock in TaskFlow."
    valid_ids = {"ev_001", "q1", "cl_001"}

    eval_result = EvaluationResult(
        per_question=[],
        evidence_consistency="high",
        consistency_rationale="Solid understanding.",
        flags=[
            Flag(
                type="potential_mismatch",
                severity="medium",
                action_text="Verify",
                refs=["ev_001"],  # Valid ref
            ),
            Flag(
                type="potential_mismatch",
                severity="low",
                action_text="Verify",
                refs=["fake_ev_999"],  # Invalid ref
            ),
        ],
        strengths=[
            Finding(text="Strong locking knowledge", refs=["ev_001", "q1"]),
            Finding(text="Unreferenced strength", refs=["invalid_ref_xyz"]),
        ],
        gaps=[],
        verification_points=[],
        interview_probes=["Ask about locking.", "Verify Postgres indexing."],
        competencies_assessed=[],
    )

    validated = validate_grounding(eval_result, valid_ids, all_answers)

    # Only flag with valid ref kept
    assert len(validated.flags) == 1
    assert validated.flags[0].refs == ["ev_001"]

    # Strength with invalid ref dropped or ref cleaned
    assert len(validated.strengths) == 1
    assert "ev_001" in validated.strengths[0].refs
