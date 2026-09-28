"""
Cost tracking and estimation service for CandidateLens.
Prices are in USD per 1,000,000 tokens.
"""

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import LLMCall

# MODEL PRICING TABLE (USD per 1M tokens)
# NOTE: verify against current OpenAI pricing
MODEL_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {
        "input_per_million": 0.15,
        "output_per_million": 0.60,
    },
    "gpt-4o": {
        "input_per_million": 2.50,
        "output_per_million": 10.00,
    },
    "text-embedding-3-small": {
        "input_per_million": 0.02,
        "output_per_million": 0.00,
    },
    # Fallback default for unknown models
    "default": {
        "input_per_million": 0.50,
        "output_per_million": 1.50,
    },
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate estimated cost in USD for a given LLM call."""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])
    input_cost = (input_tokens / 1_000_000.0) * pricing["input_per_million"]
    output_cost = (output_tokens / 1_000_000.0) * pricing["output_per_million"]
    return round(input_cost + output_cost, 6)


def get_candidate_cost(db: Session, candidate_id: str) -> float:
    """Sum total cost in USD for a specific candidate."""
    total = (
        db.query(func.sum(LLMCall.est_cost_usd))
        .filter(LLMCall.candidate_id == candidate_id)
        .scalar()
    )
    return float(total or 0.0)


def get_cost_summary(db: Session) -> dict[str, Any]:
    """Return aggregated cost metrics across all LLM calls."""
    calls = db.query(LLMCall).order_by(LLMCall.created_at.desc()).all()

    total_cost = sum(c.est_cost_usd for c in calls)
    total_calls = len(calls)
    total_input = sum(c.input_tokens for c in calls)
    total_output = sum(c.output_tokens for c in calls)

    # Unique candidates with calls
    candidate_ids = set(c.candidate_id for c in calls if c.candidate_id)
    cand_count = max(len(candidate_ids), 1)
    avg_per_cand = total_cost / cand_count if candidate_ids else 0.0
    projected_100 = avg_per_cand * 100.0

    calls_by_stage: dict[str, int] = {}
    cost_by_model: dict[str, float] = {}

    for c in calls:
        calls_by_stage[c.stage] = calls_by_stage.get(c.stage, 0) + 1
        cost_by_model[c.model] = round(cost_by_model.get(c.model, 0.0) + c.est_cost_usd, 5)

    return {
        "total_cost_usd": round(total_cost, 4),
        "total_calls": total_calls,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "avg_cost_per_candidate_usd": round(avg_per_cand, 4),
        "projected_100_candidates_usd": round(projected_100, 2),
        "calls_by_stage": calls_by_stage,
        "cost_by_model": cost_by_model,
        "recent_calls": [
            {
                "call_id": c.call_id,
                "candidate_id": c.candidate_id,
                "stage": c.stage,
                "model": c.model,
                "input_tokens": c.input_tokens,
                "output_tokens": c.output_tokens,
                "latency_ms": c.latency_ms,
                "est_cost_usd": c.est_cost_usd,
                "ok": c.ok,
                "mock": c.mock,
                "created_at": c.created_at,
            }
            for c in calls[:30]
        ],
    }
