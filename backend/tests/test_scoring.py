from app.schemas.llm import Flag
from app.services.scoring import (
    DEFAULT_WEIGHTS,
    compute_score,
    determine_band,
    determine_confidence,
    hash_scoring_inputs,
    rubric_to_100,
)


def test_rubric_to_100():
    assert rubric_to_100(1) == 0.0
    assert rubric_to_100(3) == 50.0
    assert rubric_to_100(5) == 100.0
    assert rubric_to_100(2) == 25.0
    assert rubric_to_100(4) == 75.0


def test_weights_sum_to_100():
    total_w = sum(DEFAULT_WEIGHTS.values())
    assert abs(total_w - 100.0) < 1e-5


def test_sparse_redistribution_preserves_total_weight():
    components = {k: 80.0 for k in DEFAULT_WEIGHTS}
    score, adjusted_weights = compute_score(
        components=components,
        weights=DEFAULT_WEIGHTS,
        sufficiency="sparse",
        sparse_factor=0.5,
    )
    # Total adjusted weight must sum to 100
    assert abs(sum(adjusted_weights.values()) - 100.0) < 0.1
    # Evidence weights should be halved
    assert adjusted_weights["jd_alignment"] == 10.0
    assert adjusted_weights["technical_depth_evidence"] == 7.5
    assert adjusted_weights["ownership_activity"] == 5.0
    # Assessment components should have increased
    assert adjusted_weights["technical_quality_assessment"] > DEFAULT_WEIGHTS["technical_quality_assessment"]


def test_sparse_never_needs_verification_when_assessment_is_strong():
    """AC-5: Sparse evidence alone must NEVER trigger Needs Verification when assessment is strong."""
    # Strong assessment performance: 85 score, 0 flags, sparse footprint
    band = determine_band(
        score=85.0,
        confidence="Medium",
        flags=[],
        all_critical_assessed=True,
        sufficiency="sparse",
    )
    assert band == "Strong Readiness"
    assert band != "Needs Verification"


def test_band_boundaries():
    # Strong readiness: score >= 80, no high flags, confidence >= Medium
    assert determine_band(80.0, "High", [], True) == "Strong Readiness"
    assert determine_band(85.0, "Medium", [], True) == "Strong Readiness"

    # Moderate readiness: score 60-79 or high score with Low confidence
    assert determine_band(72.0, "High", [], True) == "Moderate Readiness"
    assert determine_band(85.0, "Low", [], True) == "Moderate Readiness"

    # Needs verification: score < 60 OR unassessed critical OR 2+ high flags
    assert determine_band(59.9, "High", [], True) == "Needs Verification"
    assert determine_band(85.0, "High", [], False) == "Needs Verification"

    high_flag = Flag(
        type="potential_mismatch",
        severity="high",
        action_text="Verify",
        refs=["q1"],
    )
    assert determine_band(85.0, "High", [high_flag, high_flag], True) == "Needs Verification"


def test_confidence_reasons_and_calculation():
    conf, reason = determine_confidence(
        sufficiency="rich",
        critical_assessed=True,
        flags=[],
        avg_words=60,
    )
    assert conf == "High"
    assert "public footprint is well-documented" in reason

    # Sparse footprint caps at Medium unless critical assessment is thorough
    conf_sparse, reason_sparse = determine_confidence(
        sufficiency="sparse",
        critical_assessed=True,
        flags=[],
        avg_words=60,
    )
    assert conf_sparse == "Medium"
    assert "public footprint is sparse" in reason_sparse


def test_scoring_reproducibility():
    comp1 = {"jd_alignment": 80.0, "practical_problem_solving": 75.0}
    weights = {"jd_alignment": 20.0, "practical_problem_solving": 80.0}
    hash1 = hash_scoring_inputs(comp1, weights, "sparse")
    hash2 = hash_scoring_inputs(comp1, weights, "sparse")
    assert hash1 == hash2

    hash3 = hash_scoring_inputs(comp1, weights, "rich")
    assert hash1 != hash3
