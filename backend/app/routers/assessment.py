import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import generate_candidate_token, get_current_hr_user, verify_candidate_token
from app.config import settings
from app.db import get_db
from app.models import Audit, Candidate, Turn
from app.models import Session as DBSession
from app.schemas.api import (
    AssessmentAnswerSubmit,
    AssessmentLinkResponse,
    AssessmentNextStepOut,
    AssessmentSessionOut,
)
from app.services.assessment import count_words, get_current_question_state
from app.services.evaluation import run_evaluation_pipeline
from app.services.questions import generate_question_plan

router = APIRouter(tags=["assessment"])


def ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def resolve_assessment_session(token: str, db: Session) -> DBSession:
    """Find assessment session by token_jti, candidate_id, or signed token."""
    # 1. By token_jti
    session = db.query(DBSession).filter(DBSession.token_jti == token).first()
    if session:
        return session

    # 2. By candidate_id
    session = (
        db.query(DBSession)
        .filter(DBSession.candidate_id == token)
        .order_by(DBSession.created_at.desc())
        .first()
    )
    if session:
        return session

    # 3. By signed token
    try:
        data = verify_candidate_token(token)
        candidate_id = data.get("candidate_id")
        jti = data.get("jti")
        session = (
            db.query(DBSession)
            .filter(DBSession.candidate_id == candidate_id, DBSession.token_jti == jti)
            .first()
        )
        if session:
            return session
    except Exception:
        pass

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment session not found.")


@router.post("/candidates/{candidate_id}/assessment-link", response_model=AssessmentLinkResponse)
def create_assessment_link(
    candidate_id: str,
    db: Session = Depends(get_db),
    hr_user: str = Depends(get_current_hr_user),
):
    """Generate or return single deterministic assessment link for candidate."""
    cand = db.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    if cand.status not in ["READY", "IN_ASSESSMENT", "COMPLETED", "EVALUATING"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Candidate status is '{cand.status}'. Ingestion must finish before generating assessment."
        )

    # Check for existing session - enforce strictly 1 assessment link per candidate
    existing_session = (
        db.query(DBSession)
        .filter(DBSession.candidate_id == candidate_id)
        .order_by(DBSession.created_at.desc())
        .first()
    )

    if existing_session:
        # Extend expiration if needed
        now = datetime.now(timezone.utc)
        if ensure_utc(existing_session.expires_at) < now:
            existing_session.expires_at = now + timedelta(hours=settings.ASSESSMENT_LINK_TTL_HOURS)
            db.commit()
        link = f"{settings.FRONTEND_ORIGIN}/assess/{existing_session.token_jti}"
        return AssessmentLinkResponse(
            link=link,
            token=existing_session.token_jti,
            expires_at=existing_session.expires_at,
        )

    # Generate question plan (LLM Call 2) only ONCE
    role = cand.role
    profile = cand.profile
    competencies = role.competencies or []
    uncovered = profile.uncovered_competencies if profile else []
    evidence_items = [e.data for e in cand.evidence]
    claims = [{"claim_id": c.claim_id, "text": c.text, "scope": c.scope} for c in cand.claims]
    sufficiency = profile.sufficiency if profile else "sparse"

    question_plan = generate_question_plan(
        candidate_id=cand.candidate_id,
        role_title=role.title,
        role_family=role.role_family,
        competencies=competencies,
        uncovered_competencies=uncovered,
        evidence_items=evidence_items,
        claims=claims,
        sufficiency=sufficiency,
        db=db,
    )

    jti = secrets.token_hex(16)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.ASSESSMENT_LINK_TTL_HOURS)

    new_session = DBSession(
        candidate_id=candidate_id,
        state="NOT_STARTED",
        question_plan=[q.model_dump() for q in question_plan.questions],
        turn_count=0,
        expires_at=expires_at,
        token_jti=jti,
        used=False,
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    link = f"{settings.FRONTEND_ORIGIN}/assess/{jti}"

    audit = Audit(
        entity_id=candidate_id,
        action="ASSESSMENT_LINK_GENERATED",
        detail={"session_id": new_session.session_id, "expires_at": expires_at.isoformat()},
    )
    db.add(audit)
    db.commit()

    return AssessmentLinkResponse(
        link=link,
        token=jti,
        expires_at=expires_at,
    )


@router.get("/candidates/{candidate_id}/assessment-link", response_model=AssessmentLinkResponse)
def get_assessment_link(
    candidate_id: str,
    db: Session = Depends(get_db),
    hr_user: str = Depends(get_current_hr_user),
):
    """Retrieve existing assessment link for candidate, or generate one if not present."""
    cand = db.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    existing_session = (
        db.query(DBSession)
        .filter(DBSession.candidate_id == candidate_id)
        .order_by(DBSession.created_at.desc())
        .first()
    )
    if existing_session:
        link = f"{settings.FRONTEND_ORIGIN}/assess/{existing_session.token_jti}"
        return AssessmentLinkResponse(
            link=link,
            token=existing_session.token_jti,
            expires_at=existing_session.expires_at,
        )

    return create_assessment_link(candidate_id=candidate_id, db=db, hr_user=hr_user)


@router.get("/assessment/{token}", response_model=AssessmentSessionOut)
def get_assessment_session(token: str, db: Session = Depends(get_db)):
    """Public endpoint for candidate to view/resume assessment."""
    session = resolve_assessment_session(token, db)

    expires_at = ensure_utc(session.expires_at)
    if (expires_at and expires_at < datetime.now(timezone.utc)) or session.state == "EXPIRED":
        session.state = "EXPIRED"
        db.commit()
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="This assessment session has expired.")

    if session.state in ["SUBMITTED", "EVALUATING", "DONE"]:
        return AssessmentSessionOut(
            session_id=session.session_id,
            candidate_name=session.candidate.display_name,
            role_title=session.candidate.role.title,
            state=session.state,
            total_planned=len(session.question_plan or []),
            current_turn=session.turn_count,
            max_turns=settings.MAX_TURNS,
            question=None,
            is_followup=False,
            time_remaining_seconds=0,
        )

    if session.state == "NOT_STARTED":
        session.state = "ACTIVE"
        session.started_at = datetime.now(timezone.utc)
        session.candidate.status = "IN_ASSESSMENT"
        db.commit()

    q_state = get_current_question_state(session, db)
    now = datetime.now(timezone.utc)
    started = ensure_utc(session.started_at) or now
    elapsed_seconds = int((now - started).total_seconds())
    max_session_seconds = settings.ASSESSMENT_MAX_MINUTES * 60
    time_remaining = max(0, max_session_seconds - elapsed_seconds)

    return AssessmentSessionOut(
        session_id=session.session_id,
        candidate_name=session.candidate.display_name,
        role_title=session.candidate.role.title,
        state=session.state,
        total_planned=len(session.question_plan or []),
        current_turn=q_state["turn_no"],
        max_turns=settings.MAX_TURNS,
        question=q_state["question"],
        is_followup=q_state["is_followup"],
        time_remaining_seconds=time_remaining,
    )


@router.post("/assessment/{token}/answers", response_model=AssessmentNextStepOut)
def submit_answer(
    token: str,
    payload: AssessmentAnswerSubmit,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Candidate submits answer to current question."""
    session = resolve_assessment_session(token, db)
    if not session or session.state not in ["ACTIVE", "NOT_STARTED"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assessment session not active.")

    q_state = get_current_question_state(session, db)
    curr_question = q_state.get("question")
    if not curr_question:
        return AssessmentNextStepOut(
            status="completed",
            message="Assessment already finished.",
            question=None,
            turn_no=session.turn_count,
            is_followup=False,
        )

    # Record turn
    turn_no = session.turn_count + 1
    kind = "followup" if q_state["is_followup"] else "planned"
    q_id = curr_question.get("question_id", f"q{turn_no}")

    turn = Turn(
        session_id=session.session_id,
        turn_no=turn_no,
        question_id=q_id,
        kind=kind,
        question_text=curr_question.get("text", ""),
        answer_text=payload.answer_text.strip(),
        answer_words=count_words(payload.answer_text),
        time_taken_seconds=payload.time_taken_seconds,
    )
    db.add(turn)
    session.turn_count = turn_no
    db.commit()

    # Re-evaluate session state
    next_q_state = get_current_question_state(session, db)
    next_q = next_q_state.get("question")

    if not next_q or session.turn_count >= settings.MAX_TURNS:
        # Complete assessment
        session.state = "SUBMITTED"
        session.used = True
        session.candidate.status = "EVALUATING"
        db.commit()

        # Trigger background evaluation
        background_tasks.add_task(run_evaluation_pipeline, candidate_id)

        return AssessmentNextStepOut(
            status="completed",
            message="Thank you! Your assessment has been submitted for evaluation.",
            question=None,
            turn_no=session.turn_count,
            is_followup=False,
        )

    status_str = "follow_up" if next_q_state["is_followup"] else "next_question"
    return AssessmentNextStepOut(
        status=status_str,
        message="Answer recorded.",
        question=next_q,
        turn_no=session.turn_count + 1,
        is_followup=next_q_state["is_followup"],
    )
