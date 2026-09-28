from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth import get_current_hr_user
from app.config import settings
from app.db import get_db
from app.models import Audit, Candidate, Role
from app.schemas.api import (
    CandidateResultSummary,
    RoleCreate,
    RoleOut,
    RoleUpdateCompetencies,
)
from app.schemas.llm import JDParsingResult
from app.services.llm_client import call_structured, trim_to_budget
from app.services.prompts import JD_PARSING_SYSTEM_PROMPT
from app.services.resume_parser import extract_text_from_bytes, validate_file

router = APIRouter(prefix="/roles", tags=["roles"])


@router.post("", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role_json(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    hr_user: str = Depends(get_current_hr_user),
):
    """Create a new role from JSON payload and parse JD competencies with 1 small LLM call."""
    return _process_role_creation(
        title=payload.title,
        jd_text=payload.jd_text,
        role_family=payload.role_family,
        db=db,
    )


@router.post("/upload", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
async def create_role_upload(
    title: str = Form(...),
    role_family: str = Form("other"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    hr_user: str = Depends(get_current_hr_user),
):
    """Create a new role from uploaded JD document (PDF/DOCX/TXT)."""
    file_bytes = await file.read()
    try:
        ext = validate_file(file_bytes, file.filename or "jd.txt")
        jd_text = extract_text_from_bytes(file_bytes, ext)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse JD file: {e}"
        )

    if len(jd_text.strip()) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description text is too short or empty."
        )

    return _process_role_creation(
        title=title,
        jd_text=jd_text,
        role_family=role_family,
        db=db,
    )


def _process_role_creation(title: str, jd_text: str, role_family: str, db: Session) -> Role:
    trimmed_jd = trim_to_budget(jd_text, settings.MAX_INPUT_CHARS_EXTRACTION)

    user_prompt = f"Role Title: {title}\n\nJob Description:\n{trimmed_jd}"

    try:
        parse_result: JDParsingResult = call_structured(
            stage="jd_parsing",
            model=settings.OPENAI_MODEL_SMALL,
            system_prompt=JD_PARSING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=JDParsingResult,
            temperature=settings.LLM_TEMPERATURE_EXTRACT,
            max_output_tokens=settings.MAX_OUTPUT_TOKENS_EXTRACTION,
            is_essential=True,
            db=db,
        )
        competencies_data = [c.model_dump() for c in parse_result.competencies]
        inferred_family = parse_result.role_family
        if role_family in ["other", ""]:
            role_family = inferred_family
    except Exception:
        # Fallback if LLM parsing fails
        competencies_data = [
            {"name": "Core Technical Problem Solving", "description": "Core engineering execution", "rank": 1, "importance": "critical"},
            {"name": "System Architecture & Quality", "description": "Architectural principles", "rank": 2, "importance": "critical"},
            {"name": "Reliability & Debugging", "description": "Operational resilience", "rank": 3, "importance": "important"},
            {"name": "Communication & Collaboration", "description": "Technical communication", "rank": 4, "importance": "important"},
        ]

    role = Role(
        title=title,
        jd_text=jd_text,
        competencies=competencies_data,
        role_family=role_family,
    )
    db.add(role)
    db.commit()
    db.refresh(role)

    audit = Audit(
        entity_id=role.role_id,
        action="ROLE_CREATED",
        detail={"title": role.title, "role_family": role.role_family, "competencies_count": len(competencies_data)},
    )
    db.add(audit)
    db.commit()

    return role


@router.get("", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db), hr_user: str = Depends(get_current_hr_user)):
    return db.query(Role).order_by(Role.created_at.desc()).all()


@router.get("/{role_id}", response_model=RoleOut)
def get_role(role_id: str, db: Session = Depends(get_db), hr_user: str = Depends(get_current_hr_user)):
    role = db.query(Role).filter(Role.role_id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


@router.patch("/{role_id}/competencies", response_model=RoleOut)
def update_competencies(
    role_id: str,
    payload: RoleUpdateCompetencies,
    db: Session = Depends(get_db),
    hr_user: str = Depends(get_current_hr_user),
):
    role = db.query(Role).filter(Role.role_id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    role.competencies = [c.model_dump() for c in payload.competencies]
    db.commit()
    db.refresh(role)

    audit = Audit(
        entity_id=role.role_id,
        action="ROLE_COMPETENCIES_UPDATED",
        detail={"updated_count": len(role.competencies)},
    )
    db.add(audit)
    db.commit()

    return role


@router.get("/{role_id}/results", response_model=list[CandidateResultSummary])
def get_role_candidate_results(
    role_id: str,
    db: Session = Depends(get_db),
    hr_user: str = Depends(get_current_hr_user),
):
    candidates = (
        db.query(Candidate)
        .filter(Candidate.role_id == role_id)
        .order_by(Candidate.created_at.desc())
        .all()
    )

    results = []
    for c in candidates:
        band = c.result.band if c.result else None
        confidence = c.result.confidence if c.result else None
        score = c.result.score if c.result else None
        sufficiency = c.profile.sufficiency if c.profile else None

        results.append(
            CandidateResultSummary(
                candidate_id=c.candidate_id,
                display_name=c.display_name,
                status=c.status,
                band=band,
                confidence=confidence,
                score=score,
                sufficiency=sufficiency,
                created_at=c.created_at,
            )
        )
    return results
