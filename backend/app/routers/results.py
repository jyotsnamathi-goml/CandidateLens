from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_hr_user
from app.db import get_db
from app.models import Audit, Candidate, Result
from app.schemas.api import CandidateFullResultOut
from app.services.evaluation import run_evaluation_pipeline

router = APIRouter(tags=["results"])


@router.get("/candidates/{candidate_id}/result", response_model=CandidateFullResultOut)
def get_candidate_result(
    candidate_id: str,
    db: Session = Depends(get_db),
    hr_user: str = Depends(get_current_hr_user),
):
    """Retrieve full readiness report and scoring details for a candidate."""
    cand = db.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    res = db.query(Result).filter(Result.candidate_id == candidate_id).first()

    return CandidateFullResultOut(
        candidate_id=candidate_id,
        role_id=cand.role_id,
        status=cand.status,
        report=res.report if res else None,
        scoring_inputs_hash=res.scoring_inputs_hash if res else None,
    )


@router.post("/candidates/{candidate_id}/evaluate", status_code=status.HTTP_202_ACCEPTED)
def rerun_evaluation(
    candidate_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    hr_user: str = Depends(get_current_hr_user),
):
    """Re-run evaluation Call 3 and report assembly idempotently in the background."""
    cand = db.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    cand.status = "EVALUATING"
    db.commit()

    audit = Audit(
        entity_id=candidate_id,
        action="EVALUATION_RERUN_TRIGGERED",
        detail={"triggered_by": hr_user},
    )
    db.add(audit)
    db.commit()

    background_tasks.add_task(run_evaluation_pipeline, candidate_id)

    return {"message": f"Evaluation re-run scheduled for candidate {candidate_id}."}
