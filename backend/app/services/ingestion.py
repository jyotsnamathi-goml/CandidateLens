"""
Ingestion orchestrator service.
Executes document parsing, external data fetches (GitHub, web portfolio),
LLM Call 1 (Extraction), and deterministic evidence processing in the background.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Audit, Candidate, Claim, Evidence, Profile
from app.services.extraction import run_extraction
from app.services.github_client import GitHubClient
from app.services.linkedin_client import LinkedInClient
from app.services.relevance import match_evidence_to_competencies
from app.services.resume_parser import extract_text_from_path
from app.services.sufficiency import evaluate_sufficiency
from app.services.timeline import generate_timeline_observations
from app.services.web_fetch import fetch_portfolio_text

logger = logging.getLogger("candidatelens")


def add_log_step(candidate: Candidate, step: str, status: str, detail: str = ""):
    logs = list(candidate.ingestion_log or [])
    logs.append({
        "step": step,
        "status": status,
        "detail": detail,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    candidate.ingestion_log = logs


def run_candidate_ingestion(candidate_id: str):
    """Background task orchestrating candidate evidence ingestion."""
    db: Session = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
        if not candidate:
            logger.error(f"Candidate {candidate_id} not found for ingestion.")
            return

        role = candidate.role
        competencies = role.competencies or []

        # 1. Parse Resume
        add_log_step(candidate, "resume_parsing", "in_progress", "Parsing uploaded resume document.")
        db.commit()

        resume_text = ""
        try:
            resume_path = Path(candidate.resume_path)
            resume_text = extract_text_from_path(resume_path)
            add_log_step(candidate, "resume_parsing", "success", f"Extracted {len(resume_text)} characters.")
        except Exception as e:
            add_log_step(candidate, "resume_parsing", "failed", str(e))
            candidate.status = "FAILED"
            db.commit()
            return
        db.commit()

        # 2. Fetch GitHub
        github_data = {}
        if candidate.github_username:
            add_log_step(candidate, "github_fetch", "in_progress", f"Scanning GitHub user {candidate.github_username}.")
            db.commit()
            try:
                gh_client = GitHubClient()
                comp_names = [c.get("name", "") for c in competencies]
                github_data = gh_client.fetch_user_evidence(
                    username=candidate.github_username,
                    competencies=comp_names,
                    candidate_id=candidate.candidate_id,
                )
                top_count = len(github_data.get("top_repos", []))
                add_log_step(candidate, "github_fetch", "success", f"Identified {top_count} relevant repos.")
            except Exception as e:
                logger.warning(f"GitHub fetch failed for {candidate.candidate_id}: {e}")
                add_log_step(candidate, "github_fetch", "warning", f"GitHub scan partial/failed: {e}")
        else:
            add_log_step(candidate, "github_fetch", "success", "No GitHub username provided.")
        db.commit()

        # 3. Fetch LinkedIn
        linkedin_data = {}
        if getattr(candidate, "linkedin_url", None):
            add_log_step(candidate, "linkedin_fetch", "in_progress", f"Scanning LinkedIn profile {candidate.linkedin_url}.")
            db.commit()
            try:
                li_client = LinkedInClient()
                linkedin_data = li_client.fetch_profile_evidence(
                    url_or_username=candidate.linkedin_url,
                    candidate_id=candidate.candidate_id,
                )
                status_desc = f"Extracted profile ({linkedin_data.get('headline') or linkedin_data.get('username')})."
                add_log_step(candidate, "linkedin_fetch", "success", status_desc)
            except Exception as e:
                logger.warning(f"LinkedIn fetch failed for {candidate.candidate_id}: {e}")
                add_log_step(candidate, "linkedin_fetch", "warning", f"LinkedIn scan partial/failed: {e}")
        else:
            add_log_step(candidate, "linkedin_fetch", "success", "No LinkedIn URL provided.")
        db.commit()

        # 4. Fetch Portfolio
        portfolio_text = ""
        if candidate.portfolio_url:
            add_log_step(candidate, "portfolio_fetch", "in_progress", f"Fetching portfolio {candidate.portfolio_url}.")
            db.commit()
            try:
                portfolio_text = fetch_portfolio_text(candidate.portfolio_url)
                add_log_step(candidate, "portfolio_fetch", "success", f"Extracted {len(portfolio_text)} characters.")
            except Exception as e:
                logger.warning(f"Portfolio fetch failed for {candidate.candidate_id}: {e}")
                add_log_step(candidate, "portfolio_fetch", "warning", f"Portfolio fetch bypassed: {e}")
        else:
            add_log_step(candidate, "portfolio_fetch", "success", "No portfolio URL provided.")
        db.commit()

        # 5. LLM Call 1: Extraction
        add_log_step(candidate, "llm_extraction", "in_progress", "Running structured extraction call.")
        db.commit()

        try:
            extraction_result = run_extraction(
                candidate_id=candidate.candidate_id,
                competencies=competencies,
                resume_text=resume_text,
                github_data=github_data,
                portfolio_text=portfolio_text,
                linkedin_data=linkedin_data,
                db=db,
            )
            add_log_step(
                candidate,
                "llm_extraction",
                "success",
                f"Extracted {len(extraction_result.evidence)} evidence items and {len(extraction_result.claims)} claims.",
            )
        except Exception as e:
            logger.error(f"LLM extraction failed for candidate {candidate.candidate_id}: {e}")
            add_log_step(candidate, "llm_extraction", "failed", str(e))
            candidate.status = "FAILED"
            db.commit()
            return
        db.commit()

        # 5. Persist Evidence & Claims
        db.query(Evidence).filter(Evidence.candidate_id == candidate.candidate_id).delete()
        db.query(Claim).filter(Claim.candidate_id == candidate.candidate_id).delete()

        for ev in extraction_result.evidence:
            ev_row = Evidence(
                candidate_id=candidate.candidate_id,
                evidence_id=ev.evidence_id,
                type=ev.type,
                data=ev.model_dump(),
                provenance=ev.provenance,
            )
            db.add(ev_row)

        for cl in extraction_result.claims:
            cl_row = Claim(
                candidate_id=candidate.candidate_id,
                claim_id=cl.claim_id,
                text=cl.text,
                scope=cl.scope,
                linked_evidence=cl.linked_evidence,
                verification="pending",
            )
            db.add(cl_row)

        db.commit()

        # 6. Deterministic Processing: Relevance, Timeline, Sufficiency
        add_log_step(candidate, "deterministic_processing", "in_progress", "Computing relevance, timeline, and sufficiency.")
        db.commit()

        relevance_map = match_evidence_to_competencies(competencies, extraction_result.evidence)
        timeline_obs = generate_timeline_observations(extraction_result.evidence)
        sufficiency, uncovered = evaluate_sufficiency(extraction_result.evidence, competencies, relevance_map)

        db.query(Profile).filter(Profile.candidate_id == candidate.candidate_id).delete()
        profile_row = Profile(
            candidate_id=candidate.candidate_id,
            sufficiency=sufficiency,
            uncovered_competencies=uncovered,
            timeline=[obs.model_dump() for obs in timeline_obs],
            relevance=relevance_map,
            github_metrics=github_data,
        )
        db.add(profile_row)

        candidate.status = "READY"
        add_log_step(candidate, "deterministic_processing", "success", f"Classified sufficiency as {sufficiency.upper()}.")

        audit = Audit(
            entity_id=candidate.candidate_id,
            action="INGESTION_COMPLETED",
            detail={"status": "READY", "sufficiency": sufficiency, "uncovered_count": len(uncovered)},
        )
        db.add(audit)
        db.commit()
        logger.info(f"Ingestion completed successfully for candidate {candidate.candidate_id}.")

    except Exception as exc:
        logger.exception(f"Unexpected error during ingestion of candidate {candidate_id}: {exc}")
        if candidate:
            candidate.status = "FAILED"
            add_log_step(candidate, "ingestion_fatal", "failed", str(exc))
            db.commit()
    finally:
        db.close()
