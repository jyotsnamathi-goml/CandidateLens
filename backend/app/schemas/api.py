from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.domain import IngestionStepLog, ReadinessReport, TimelineObservation
from app.schemas.llm import JDCompetency


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


# --- Auth ---
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# --- Roles ---
class RoleCreate(BaseModel):
    title: str = Field(..., min_length=2)
    jd_text: str = Field(..., min_length=20)
    role_family: Literal["ml", "frontend", "backend", "other"] = "other"


class RoleUpdateCompetencies(BaseModel):
    competencies: list[JDCompetency]


class RoleOut(BaseModel):
    role_id: str
    title: str
    jd_text: str
    competencies: list[JDCompetency]
    role_family: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Candidates ---
class CandidateCreate(BaseModel):
    display_name: str
    github_username: str | None = None
    portfolio_url: str | None = None
    consent: bool = Field(..., description="Must be true to proceed with ingestion")


class CandidateOut(BaseModel):
    candidate_id: str
    role_id: str
    display_name: str
    github_username: str | None = None
    portfolio_url: str | None = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IngestionStatusOut(BaseModel):
    candidate_id: str
    status: str
    steps: list[IngestionStepLog]


class EvidenceListOut(BaseModel):
    candidate_id: str
    evidence: list[dict[str, Any]]
    claims: list[dict[str, Any]]
    sufficiency: str


class TimelineOut(BaseModel):
    candidate_id: str
    timeline: list[TimelineObservation]


# --- Assessment ---
class AssessmentLinkResponse(BaseModel):
    link: str
    token: str
    expires_at: datetime


class AssessmentSessionOut(BaseModel):
    session_id: str
    candidate_name: str
    role_title: str
    state: str
    total_planned: int = 6
    current_turn: int
    max_turns: int
    question: dict[str, Any] | None = None  # question_id, kind, text, snippet if any
    is_followup: bool = False
    time_remaining_seconds: int


class AssessmentAnswerSubmit(BaseModel):
    answer_text: str = Field(..., min_length=1)
    time_taken_seconds: int = 0


class AssessmentNextStepOut(BaseModel):
    status: Literal["next_question", "follow_up", "completed", "expired"]
    message: str
    question: dict[str, Any] | None = None
    turn_no: int
    is_followup: bool = False


# --- Notes ---
class HRNoteCreate(BaseModel):
    text: str = Field(..., min_length=1)
    is_override: bool = False


class HRNoteOut(BaseModel):
    note_id: str
    candidate_id: str
    author: str
    text: str
    is_override: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Results & Reports ---
class CandidateResultSummary(BaseModel):
    candidate_id: str
    display_name: str
    status: str
    band: str | None = None
    confidence: str | None = None
    score: float | None = None
    sufficiency: str | None = None
    created_at: datetime


class CandidateFullResultOut(BaseModel):
    candidate_id: str
    role_id: str
    status: str
    report: ReadinessReport | None = None
    scoring_inputs_hash: str | None = None


# --- Admin Costs ---
class LLMCallItem(BaseModel):
    call_id: str
    candidate_id: str | None
    stage: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    est_cost_usd: float
    ok: bool
    mock: bool
    created_at: datetime


class CostSummaryOut(BaseModel):
    total_cost_usd: float
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    avg_cost_per_candidate_usd: float
    projected_100_candidates_usd: float
    calls_by_stage: dict[str, int]
    cost_by_model: dict[str, float]
    recent_calls: list[LLMCallItem]
