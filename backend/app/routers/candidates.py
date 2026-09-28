import shutil
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.auth import get_current_hr_user
from app.config import settings
from app.db import get_db
from app.models import Audit, Candidate, Claim, Evidence, HRNote, Profile, Role
from app.schemas.api import (
    CandidateOut,
    EvidenceListOut,
    HRNoteCreate,
    HRNoteOut,
    IngestionStatusOut,
    TimelineOut,
)
from app.services.ingestion import run_candidate_ingestion
from app.services.resume_parser import validate_file

router = APIRouter(tags=["candidates"])


@router.post("/roles/{role_id}/candidates", response_model=CandidateOut, status_code=status.HTTP_201_CREATED)
async def create_candidate(
    role_id: str,
    background_tasks: BackgroundTasks,
    display_name: str = Form(...),
    consent: bool = Form(...),
    github_username: Optional[str] = Form(None),
    portfolio_url: Optional[str] = Form(None),
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
    hr_user: str = Depends(get_current_hr_user),
):
    """
    Register candidate and trigger background ingestion.
    Requires explicit consent=true.
    """
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate consent is strictly required before ingestion."
        )

    role = db.query(Role).filter(Role.role_id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    file_bytes = await resume.read()
    try:
        ext = validate_file(file_bytes, resume.filename or "resume.pdf")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    candidate_id = f"c_{uuid.uuid4().hex[:12]}"
    cand_upload_dir = settings.uploads_path / candidate_id
    cand_upload_dir.mkdir(parents=True, exist_ok=True)

    dest_file = cand_upload_dir / f"resume.{ext}"
    with open(dest_file, "wb") as f:
        f.write(file_bytes)

    retention_until = datetime.now(timezone.utc) + timedelta(days=settings.RETENTION_DAYS)

    consent_record = {
        "accepted": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scope": ["resume", "github_public", "portfolio"],
    }

    candidate = Candidate(
        candidate_id=candidate_id,
        role_id=role_id,
        display_name=display_name.strip(),
        github_username=github_username.strip() if github_username else None,
        portfolio_url=portfolio_url.strip() if portfolio_url else None,
        resume_path=str(dest_file),
        consent=consent_record,
        status="INGESTING",
        ingestion_log=[],
        retention_until=retention_until,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    audit = Audit(
        entity_id=candidate.candidate_id,
        action="CANDIDATE_CREATED",
        detail={"role_id": role_id, "display_name": display_name},
    )
    db.add(audit)
    db.commit()

    # Launch ingestion in background
    background_tasks.add_task(run_candidate_ingestion, candidate_id)

    return candidate


@router.get("/candidates/{candidate_id}", response_model=CandidateOut)
def get_candidate(
    candidate_id: str,
    db: Session = Depends(get_db),
    hr_user: str = Depends(get_current_hr_user),
):
    cand = db.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return cand


@router.get("/candidates/{candidate_id}/ingestion", response_model=IngestionStatusOut)
def get_candidate_ingestion_status(
    candidate_id: str,
    db: Session = Depends(get_db),
    hr_user: str = Depends(get_current_hr_user),
):
    cand = db.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return IngestionStatusOut(
        candidate_id=cand.candidate_id,
        status=cand.status,
        steps=cand.ingestion_log or [],
    )


@router.get("/candidates/{candidate_id}/evidence", response_model=EvidenceListOut)
def get_candidate_evidence(
    candidate_id: str,
    db: Session = Depends(get_db),
    hr_user: str = Depends(get_current_hr_user),
):
    cand = db.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    ev_rows = db.query(Evidence).filter(Evidence.candidate_id == candidate_id).all()
    cl_rows = db.query(Claim).filter(Claim.candidate_id == candidate_id).all()
    prof = db.query(Profile).filter(Profile.candidate_id == candidate_id).first()

    return EvidenceListOut(
        candidate_id=candidate_id,
        evidence=[e.data for e in ev_rows],
        claims=[
            {
                "claim_id": c.claim_id,
                "text": c.text,
                "scope": c.scope,
                "linked_evidence": c.linked_evidence,
                "verification": c.verification,
            }
            for c in cl_rows
        ],
        sufficiency=prof.sufficiency if prof else "sparse",
    )


@router.get("/candidates/{candidate_id}/timeline", response_model=TimelineOut)
def get_candidate_timeline(
    candidate_id: str,
    db: Session = Depends(get_db),
    hr_user: str = Depends(get_current_hr_user),
):
    prof = db.query(Profile).filter(Profile.candidate_id == candidate_id).first()
    if not prof:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not generated yet")
    return TimelineOut(candidate_id=candidate_id, timeline=prof.timeline or [])


@router.post("/candidates/{candidate_id}/notes", response_model=HRNoteOut)
def add_candidate_note(
    candidate_id: str,
    payload: HRNoteCreate,
    db: Session = Depends(get_db),
    hr_user: str = Depends(get_current_hr_user),
):
    cand = db.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    note = HRNote(
        candidate_id=candidate_id,
        author=hr_user,
        text=payload.text,
        is_override=payload.is_override,
    )
    db.add(note)

    audit = Audit(
        entity_id=candidate_id,
        action="NOTE_ADDED",
        detail={"is_override": payload.is_override, "author": hr_user},
    )
    db.add(audit)
    db.commit()
    db.refresh(note)
    return note


@router.delete("/candidates/{candidate_id}", status_code=status.HTTP_200_OK)
def delete_candidate(
    candidate_id: str,
    db: Session = Depends(get_db),
    hr_user: str = Depends(get_current_hr_user),
):
    """Delete all candidate data: DB records, files, and artifacts. Logs audit entry."""
    cand = db.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    # Clean file directories
    upload_dir = settings.uploads_path / candidate_id
    if upload_dir.exists():
        shutil.rmtree(upload_dir, ignore_errors=True)

    artifact_dir = settings.artifacts_path / candidate_id
    if artifact_dir.exists():
        shutil.rmtree(artifact_dir, ignore_errors=True)

    db.delete(cand)

    audit = Audit(
        entity_id=candidate_id,
        action="CANDIDATE_DELETED",
        detail={"purged_by": hr_user},
    )
    db.add(audit)
    db.commit()

    return {"message": f"Candidate {candidate_id} and all related artifacts deleted."}
