from typing import Literal

from pydantic import BaseModel, Field


# --- JD Parsing (1 per role) ---
class JDCompetency(BaseModel):
    name: str = Field(..., description="Name of competency")
    description: str = Field(..., description="Short description of what is expected")
    rank: int = Field(..., ge=1, le=10, description="Priority rank 1 to 6")
    importance: Literal["critical", "important", "nice_to_have"] = "important"


class JDParsingResult(BaseModel):
    role_title: str
    role_family: Literal["ml", "frontend", "backend", "other"]
    competencies: list[JDCompetency] = Field(..., min_length=4, max_length=6)


# --- LLM Call 1: Extraction ---
class EvidenceAttributes(BaseModel):
    jd_relevance: float = Field(..., ge=0.0, le=1.0)
    technical_depth: float = Field(..., ge=0.0, le=1.0)
    ownership: float = Field(..., ge=0.0, le=1.0)
    collaboration: float = Field(..., ge=0.0, le=1.0)
    recency: float = Field(..., ge=0.0, le=1.0)
    evidence_strength: float = Field(..., ge=0.0, le=1.0)


class EvidenceItem(BaseModel):
    evidence_id: str
    type: Literal["project", "work_experience", "contribution", "publication", "other"]
    title: str
    technologies: list[str] = Field(default_factory=list)
    role: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    date_start: str | None = None
    date_end: str | None = None
    outcomes: list[str] = Field(default_factory=list)
    provenance: Literal["candidate_provided", "public_evidence", "model_inference"]
    source_url: str | None = None
    attributes: EvidenceAttributes


class Claim(BaseModel):
    claim_id: str
    text: str
    scope: Literal["designed", "led", "built", "contributed", "used", "optimized", "other"]
    linked_evidence: list[str] = Field(default_factory=list)


class CompetencyCoverage(BaseModel):
    competency: str
    covered_by: list[str] = Field(default_factory=list)
    note: str = ""


class ExtractionResult(BaseModel):
    evidence: list[EvidenceItem] = Field(..., max_length=8)
    claims: list[Claim] = Field(..., max_length=12)
    competency_coverage: list[CompetencyCoverage]
    notable_gaps: list[str] = Field(default_factory=list)


# --- LLM Call 2: Question Planning ---
class PlannedQuestion(BaseModel):
    question_id: str
    kind: Literal["jd_scenario", "project_specific", "verification"]
    competency: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    text: str
    what_good_looks_like: list[str] = Field(default_factory=list)
    follow_up_if_vague: str
    follow_up_if_strong: str | None = None


class QuestionPlan(BaseModel):
    questions: list[PlannedQuestion] = Field(..., min_length=6, max_length=6)


# --- Optional Adaptive Follow-up ---
class AdaptiveFollowup(BaseModel):
    follow_up_text: str
    reason: str


# --- LLM Call 3: Evaluation ---
class DimensionScore(BaseModel):
    score: int = Field(..., ge=1, le=5)
    quote: str = Field(..., description="Verbatim quote from candidate answer justifying the score")


class QuestionEvaluation(BaseModel):
    question_id: str
    technical_correctness: DimensionScore
    technical_depth: DimensionScore
    mechanism: DimensionScore
    trade_offs: DimensionScore
    problem_solving: DimensionScore
    communication: DimensionScore
    specificity: DimensionScore
    competency: str | None = None


class Flag(BaseModel):
    type: Literal["potential_mismatch", "claim_scope_gap", "insufficient_evidence"]
    severity: Literal["low", "medium", "high"]
    public_evidence: str | None = None
    candidate_statement: str | None = None
    refs: list[str] = Field(default_factory=list)
    action_text: str


class Finding(BaseModel):
    text: str
    refs: list[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    per_question: list[QuestionEvaluation]
    evidence_consistency: Literal["high", "medium", "low"]
    consistency_rationale: str
    flags: list[Flag] = Field(default_factory=list)
    strengths: list[Finding] = Field(..., min_length=1, max_length=5)
    gaps: list[Finding] = Field(default_factory=list)
    verification_points: list[Finding] = Field(default_factory=list)
    interview_probes: list[str] = Field(..., min_length=2, max_length=4)
    competencies_assessed: list[str] = Field(default_factory=list)
