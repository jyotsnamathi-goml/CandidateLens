import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def gen_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class Role(Base):
    __tablename__ = "roles"

    role_id = Column(String(32), primary_key=True, default=lambda: gen_id("r"))
    title = Column(String(255), nullable=False)
    jd_text = Column(Text, nullable=False)
    competencies = Column(JSON, nullable=False, default=list)  # ranked list of 4-6
    weights = Column(JSON, nullable=True)  # custom component weights if overridden
    role_family = Column(String(50), nullable=False, default="other")  # ml, frontend, backend, other
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    candidates = relationship("Candidate", back_populates="role", cascade="all, delete-orphan")


class Candidate(Base):
    __tablename__ = "candidates"

    candidate_id = Column(String(32), primary_key=True, default=lambda: gen_id("c"))
    role_id = Column(String(32), ForeignKey("roles.role_id", ondelete="CASCADE"), nullable=False)
    display_name = Column(String(255), nullable=False)
    github_username = Column(String(100), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    resume_path = Column(String(500), nullable=False)
    consent = Column(JSON, nullable=False, default=dict)  # accepted, timestamp, scope
    status = Column(String(50), nullable=False, default="INGESTING")  # INGESTING, READY, IN_ASSESSMENT, COMPLETED, FAILED
    ingestion_log = Column(JSON, nullable=False, default=list)
    retention_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    role = relationship("Role", back_populates="candidates")
    evidence = relationship("Evidence", back_populates="candidate", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="candidate", cascade="all, delete-orphan")
    profile = relationship("Profile", back_populates="candidate", uselist=False, cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="candidate", cascade="all, delete-orphan")
    result = relationship("Result", back_populates="candidate", uselist=False, cascade="all, delete-orphan")
    notes = relationship("HRNote", back_populates="candidate", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String(32), ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=False)
    evidence_id = Column(String(64), nullable=False)  # ev_001
    type = Column(String(50), nullable=False)  # project, work_experience, contribution, etc.
    data = Column(JSON, nullable=False, default=dict)
    provenance = Column(String(50), nullable=False)  # candidate_provided, public_evidence, model_inference
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    candidate = relationship("Candidate", back_populates="evidence")


class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String(32), ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=False)
    claim_id = Column(String(64), nullable=False)  # cl_001
    text = Column(Text, nullable=False)
    scope = Column(String(50), nullable=False)  # designed, led, built, contributed, used, etc.
    linked_evidence = Column(JSON, nullable=False, default=list)  # evidence_ids
    verification = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    candidate = relationship("Candidate", back_populates="claims")


class Profile(Base):
    __tablename__ = "profile"

    candidate_id = Column(String(32), ForeignKey("candidates.candidate_id", ondelete="CASCADE"), primary_key=True)
    sufficiency = Column(String(20), nullable=False, default="sparse")  # rich, partial, sparse
    uncovered_competencies = Column(JSON, nullable=False, default=list)
    timeline = Column(JSON, nullable=False, default=list)
    relevance = Column(JSON, nullable=False, default=dict)
    github_metrics = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    candidate = relationship("Candidate", back_populates="profile")


class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(String(32), primary_key=True, default=lambda: gen_id("sess"))
    candidate_id = Column(String(32), ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=False)
    state = Column(String(30), nullable=False, default="NOT_STARTED")  # NOT_STARTED, ACTIVE, SUBMITTED, EVALUATING, DONE, EXPIRED
    question_plan = Column(JSON, nullable=False, default=list)
    turn_count = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    token_jti = Column(String(64), unique=True, nullable=False)
    used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    candidate = relationship("Candidate", back_populates="sessions")
    turns = relationship("Turn", back_populates="session", cascade="all, delete-orphan")


class Turn(Base):
    __tablename__ = "turns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(32), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False)
    turn_no = Column(Integer, nullable=False)
    question_id = Column(String(32), nullable=False)
    kind = Column(String(20), nullable=False)  # planned, followup
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    answer_words = Column(Integer, nullable=False, default=0)
    time_taken_seconds = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    session = relationship("Session", back_populates="turns")


class Result(Base):
    __tablename__ = "results"

    candidate_id = Column(String(32), ForeignKey("candidates.candidate_id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(String(32), ForeignKey("roles.role_id", ondelete="CASCADE"), nullable=False)
    evaluation = Column(JSON, nullable=False, default=dict)
    component_scores = Column(JSON, nullable=False, default=dict)
    score = Column(Float, nullable=False, default=0.0)
    band = Column(String(50), nullable=False)  # Strong Readiness, Moderate Readiness, Needs Verification
    confidence = Column(String(20), nullable=False)  # High, Medium, Low
    confidence_reason = Column(Text, nullable=False)
    flags = Column(JSON, nullable=False, default=list)
    report = Column(JSON, nullable=False, default=dict)
    scoring_inputs_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    candidate = relationship("Candidate", back_populates="result")


class LLMCall(Base):
    __tablename__ = "llm_calls"

    call_id = Column(String(32), primary_key=True, default=lambda: gen_id("call"))
    candidate_id = Column(String(32), nullable=True, index=True)
    stage = Column(String(50), nullable=False)  # jd_parsing, extraction, question_plan, followup, evaluation
    model = Column(String(100), nullable=False)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    latency_ms = Column(Integer, nullable=False, default=0)
    est_cost_usd = Column(Float, nullable=False, default=0.0)
    ok = Column(Boolean, nullable=False, default=True)
    retry_count = Column(Integer, nullable=False, default=0)
    mock = Column(Boolean, nullable=False, default=False)
    prompt_version = Column(String(20), nullable=False, default="v1")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class HRNote(Base):
    __tablename__ = "hr_notes"

    note_id = Column(String(32), primary_key=True, default=lambda: gen_id("note"))
    candidate_id = Column(String(32), ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=False)
    author = Column(String(100), nullable=False, default="HR")
    text = Column(Text, nullable=False)
    is_override = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    candidate = relationship("Candidate", back_populates="notes")


class Audit(Base):
    __tablename__ = "audit"

    audit_id = Column(String(32), primary_key=True, default=lambda: gen_id("aud"))
    entity_id = Column(String(64), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    detail = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
