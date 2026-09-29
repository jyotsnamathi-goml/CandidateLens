"""
OpenAI LLM Client wrapper for CandidateLens.
Features:
- Structured outputs using Pydantic schemas.
- Single automatic retry on schema validation failure with error hint.
- Mock mode support with zero API key requirement.
- Cost and token logging to DB and structured logs.
- Hard token budget trimming.
- Rate-limit backoff and timeouts.
"""

import json
import logging
import time
from pathlib import Path
from typing import Type, TypeVar

import httpx
from openai import APIError, LengthFinishReasonError, OpenAI, RateLimitError
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.models import LLMCall
from app.services.costs import estimate_cost, get_candidate_cost
from app.services.prompts import PROMPT_VERSION

logger = logging.getLogger("candidatelens")

T = TypeVar("T", bound=BaseModel)

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


class LLMStructuredOutputError(Exception):
    """Raised when LLM output fails schema validation after retry."""
    pass


class CostBudgetExceededError(Exception):
    """Raised when candidate cost budget cap is exceeded for a non-essential call."""
    pass


def trim_to_budget(text: str, max_chars: int) -> str:
    """Trim text to max_chars at paragraph or sentence boundary."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    # Try to cut at last newline
    last_para = truncated.rfind("\n\n")
    if last_para > max_chars * 0.7:
        return truncated[:last_para].rstrip() + "\n\n[truncated]"
    last_nl = truncated.rfind("\n")
    if last_nl > max_chars * 0.7:
        return truncated[:last_nl].rstrip() + "\n[truncated]"
    last_period = truncated.rfind(". ")
    if last_period > max_chars * 0.7:
        return truncated[:last_period + 1] + " [truncated]"
    return truncated.rstrip() + "... [truncated]"


def _is_mock_enabled() -> bool:
    if settings.LLM_MOCK:
        return True
    if not settings.OPENAI_API_KEY or "placeholder" in settings.OPENAI_API_KEY.lower():
        return True
    return False


def _get_mock_response(stage: str, schema: Type[T]) -> T:
    fixture_map = {
        "jd_parsing": "mock_jd_competencies.json",
        "extraction": "mock_extraction.json",
        "question_plan": "mock_question_plan.json",
        "evaluation": "mock_evaluation.json",
    }
    filename = fixture_map.get(stage)
    if not filename:
        raise ValueError(f"No mock fixture defined for stage: {stage}")

    file_path = FIXTURES_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Fixture file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return schema.model_validate(data)


def log_llm_call(
    db: Session | None,
    candidate_id: str | None,
    stage: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: int,
    ok: bool = True,
    retry_count: int = 0,
    mock: bool = False,
) -> LLMCall:
    cost = estimate_cost(model, input_tokens, output_tokens) if not mock else 0.0
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    call_record = LLMCall(
        candidate_id=candidate_id,
        stage=stage,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        est_cost_usd=cost,
        ok=ok,
        retry_count=retry_count,
        mock=mock,
        prompt_version=PROMPT_VERSION,
    )
    db.add(call_record)
    db.commit()
    db.refresh(call_record)

    logger.info(
        "LLM Call executed",
        extra={
            "candidate_id": candidate_id,
            "stage": stage,
            "model": model,
            "metrics": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": latency_ms,
                "cost_usd": cost,
                "mock": mock,
            },
        },
    )

    if own_session:
        db.close()

    return call_record


def call_structured(
    stage: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    schema: Type[T],
    candidate_id: str | None = None,
    temperature: float = 0.2,
    max_output_tokens: int | None = None,
    is_essential: bool = True,
    db: Session | None = None,
) -> T:
    """
    Execute a structured LLM call with schema validation, retry, and cost tracking.
    """
    # 1. Budget check
    if candidate_id and db:
        curr_cost = get_candidate_cost(db, candidate_id)
        if curr_cost >= settings.PER_CANDIDATE_COST_CAP_USD:
            if not is_essential:
                logger.warning(
                    f"Candidate {candidate_id} cost ${curr_cost:.4f} exceeded cap ${settings.PER_CANDIDATE_COST_CAP_USD}. Skipping non-essential call."
                )
                raise CostBudgetExceededError(f"Candidate {candidate_id} cost budget exceeded.")
            else:
                logger.warning(
                    f"Candidate {candidate_id} cost ${curr_cost:.4f} exceeded cap ${settings.PER_CANDIDATE_COST_CAP_USD}, but call is essential. Proceeding."
                )

    # 2. Check Mock Mode
    if _is_mock_enabled():
        start_time = time.time()
        result = _get_mock_response(stage, schema)
        latency_ms = int((time.time() - start_time) * 1000)
        # Approximate mock token counts
        input_tokens = len(system_prompt + user_prompt) // 4
        output_tokens = len(result.model_dump_json()) // 4
        log_llm_call(
            db=db,
            candidate_id=candidate_id,
            stage=stage,
            model=f"mock-{model}",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            ok=True,
            retry_count=0,
            mock=True,
        )
        return result

    # 3. Real OpenAI Call with retry
    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        http_client=httpx.Client(timeout=60.0),
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    total_retries = 0
    start_time = time.time()
    last_err: Exception | None = None

    current_max_tokens = max_output_tokens
    for attempt in range(2):  # initial attempt + 1 retry on parse error
        try:
            # API retry with backoff for rate limits/5xx
            api_attempts = 0
            while api_attempts < 3:
                try:
                    kwargs = {
                        "model": model,
                        "messages": messages,
                        "response_format": schema,
                        "temperature": temperature,
                    }
                    if current_max_tokens:
                        kwargs["max_tokens"] = current_max_tokens

                    completion = client.beta.chat.completions.parse(**kwargs)
                    break
                except (RateLimitError, APIError) as e:
                    api_attempts += 1
                    if api_attempts >= 3:
                        raise e
                    sleep_s = 2.0 ** api_attempts
                    logger.warning(f"OpenAI API error on attempt {api_attempts}: {e}. Retrying in {sleep_s}s...")
                    time.sleep(sleep_s)

            parsed = completion.choices[0].message.parsed
            if parsed is None:
                refusal = completion.choices[0].message.refusal
                raise ValueError(f"Model refused or returned null parsed object: {refusal}")

            latency_ms = int((time.time() - start_time) * 1000)
            in_tok = completion.usage.prompt_tokens if completion.usage else len(str(messages)) // 4
            out_tok = completion.usage.completion_tokens if completion.usage else 500

            log_llm_call(
                db=db,
                candidate_id=candidate_id,
                stage=stage,
                model=model,
                input_tokens=in_tok,
                output_tokens=out_tok,
                latency_ms=latency_ms,
                ok=True,
                retry_count=total_retries,
                mock=False,
            )
            return parsed

        except LengthFinishReasonError as err:
            last_err = err
            total_retries += 1
            if current_max_tokens:
                current_max_tokens = min(int(current_max_tokens * 1.5), 8192)
            logger.warning(
                f"Length limit reached on attempt {attempt + 1} for stage '{stage}'. "
                f"Increased max_tokens to {current_max_tokens}. Retrying with conciseness prompt."
            )
            messages.append({
                "role": "user",
                "content": "Previous output was cut off because it exceeded the max token limit. "
                           "Please output complete valid JSON matching the schema, keeping bullet points concise.",
            })

        except (ValidationError, ValueError) as err:
            last_err = err
            total_retries += 1
            logger.warning(f"Structured output parse error on attempt {attempt + 1}: {err}. Retrying once with hint.")
            messages.append({
                "role": "user",
                "content": f"Previous output was invalid: {err}. Please return valid JSON strictly complying with the schema.",
            })

    # If failed after retry
    latency_ms = int((time.time() - start_time) * 1000)
    log_llm_call(
        db=db,
        candidate_id=candidate_id,
        stage=stage,
        model=model,
        input_tokens=len(str(messages)) // 4,
        output_tokens=0,
        latency_ms=latency_ms,
        ok=False,
        retry_count=total_retries,
        mock=False,
    )
    raise LLMStructuredOutputError(f"Failed to produce valid structured output for stage {stage}: {last_err}")
