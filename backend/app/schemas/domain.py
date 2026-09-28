from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.llm import EvidenceItem, Finding, Flag, QuestionEvaluation


class ConsentData(BaseModel):
    accepted: bool
    timestamp: str
    scope: list[str] = Field(default_factory=lambda: ["resume", "github_public", "portfolio"])


class IngestionStepLog(BaseModel):
    step: str
    status: Literal["pending", "in_progress", "success", "warning", "failed"]
    detail: str = ""
    timestamp: str = ""


class GitHubMetrics(BaseModel):
    username: str
    repos_examined: int = 0
    top_repos: list[dict[str, Any]] = Field(default_factory=list)
    total_commits_scanned: int = 0
    user_commit_share: float = 0.0
    last_commit_date: str | None = None
    original_repos_count: int = 0
    fork_count: int = 0


class TimelineObservation(BaseModel):
    observation: str
    evidence_refs: list[str] = Field(default_factory=list)
    trend_type: Literal["complexity", "consistency", "recency", "collaboration"]


class ScoreBreakdownItem(BaseModel):
    name: str
    label: str
    weight: float
    score: float  # 0 to 100
    weighted_score: float
    inputs: dict[str, Any] = Field(default_factory=dict)
    source_description: str


class ReadinessReport(BaseModel):
    candidate_id: str
    role_id: str
    role_title: str
    display_name: str
    band: Literal["Strong Readiness", "Moderate Readiness", "Needs Verification"]
    confidence: Literal["High", "Medium", "Low"]
    confidence_reason: str
    score: float
    disclaimer: str = "Candidate Readiness Signal, not a hiring decision."
    component_breakdown: list[ScoreBreakdownItem]
    sufficiency: Literal["rich", "partial", "sparse"]
    sufficiency_impact: str
    strengths: list[Finding]
    verification_points: list[Finding]
    flags: list[Flag]
    timeline_observations: list[TimelineObservation]
    evidence_items: list[EvidenceItem]
    assessment_analysis: list[QuestionEvaluation]
    interview_probes: list[str]
    notes: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str
