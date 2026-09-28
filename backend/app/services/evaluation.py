"""
Evaluation Service (LLM Call 3).
Evaluates all assessment answers concurrently against anchored 1-5 rubrics,
runs grounding and quote validators, and drives deterministic scoring and report generation.
"""

import json
import logging

from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.models import Audit, Candidate, Evidence, Profile, Result, Turn
from app.models import Session as DBSession
from app.schemas.domain import TimelineObservation
from app.schemas.llm import EvaluationResult, EvidenceItem
from app.services.llm_client import call_structured, trim_to_budget
from app.services.prompts import EVALUATION_SYSTEM_PROMPT
from app.services.report import build_readiness_report
from app.services.scoring import (
    calculate_component_scores,
    compute_score,
    determine_band,
    determine_confidence,
    hash_scoring_inputs,
)
from app.services.validators import validate_grounding

logger = logging.getLogger("candidatelens")


def run_evaluation_pipeline(candidate_id: str):
    """Background task executing Call 3, validation, scoring, and report assembly."""
    db: Session = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
        if not candidate:
            logger.error(f"Candidate {candidate_id} not found for evaluation.")
            return

        session = (
            db.query(DBSession)
            .filter(DBSession.candidate_id == candidate_id)
            .order_by(DBSession.created_at.desc())
            .first()
        )
        if not session:
            logger.error(f"No assessment session found for candidate {candidate_id}.")
            return

        turns = (
            db.query(Turn)
            .filter(Turn.session_id == session.session_id)
            .order_by(Turn.turn_no.asc())
            .all()
        )
        if not turns:
            logger.warning(f"No turns recorded for candidate {candidate_id}.")
            return

        evidence_rows = db.query(Evidence).filter(Evidence.candidate_id == candidate_id).all()
        evidence_items: list[EvidenceItem] = []
        for e in evidence_rows:
            try:
                evidence_items.append(EvidenceItem.model_validate(e.data))
            except Exception:
                pass

        profile = db.query(Profile).filter(Profile.candidate_id == candidate_id).first()
        sufficiency = profile.sufficiency if profile else "sparse"
        relevance_map = profile.relevance if profile else {}
        github_metrics = profile.github_metrics if profile else {}
        timeline_obs = [TimelineObservation.model_validate(t) for t in (profile.timeline or [])] if profile else []

        role = candidate.role
        competencies = role.competencies or []

        # 1. Format candidate answers
        all_answers_text = ""
        turns_payload = []
        for t in turns:
            turns_payload.append({
                "turn_no": t.turn_no,
                "question_id": t.question_id,
                "kind": t.kind,
                "question_text": t.question_text,
                "answer_text": t.answer_text,
            })
            all_answers_text += f"\n{t.answer_text}"

        condensed_evidence = [
            {
                "id": ev.evidence_id,
                "title": ev.title,
                "provenance": ev.provenance,
                "tech": ev.technologies[:4],
                "strength": ev.attributes.evidence_strength,
            }
            for ev in evidence_items
        ]

        user_prompt = f"""Role: {role.title}
Competencies:
{json.dumps(competencies, indent=2)}

<candidate_evidence>
{json.dumps(condensed_evidence, indent=2)}
</candidate_evidence>

<candidate_answers>
{json.dumps(turns_payload, indent=2)}
</candidate_answers>

Evaluate all questions against 1-5 rubrics.
Include verbatim quotes for all dimension scores > 2.
Return ONLY JSON matching the schema.
"""
        trimmed_prompt = trim_to_budget(user_prompt, settings.MAX_INPUT_CHARS_EVALUATION)

        # 2. LLM Call 3: Evaluation
        try:
            eval_result: EvaluationResult = call_structured(
                stage="evaluation",
                model=settings.OPENAI_MODEL_STRONG,
                system_prompt=EVALUATION_SYSTEM_PROMPT,
                user_prompt=trimmed_prompt,
                schema=EvaluationResult,
                candidate_id=candidate_id,
                temperature=settings.LLM_TEMPERATURE_EVAL,
                max_output_tokens=settings.MAX_OUTPUT_TOKENS_EVALUATION,
                is_essential=True,
                db=db,
            )
        except Exception as e:
            logger.error(f"Evaluation LLM Call 3 failed for candidate {candidate_id}: {e}")
            candidate.status = "EVALUATION_FAILED"
            db.commit()
            return

        # 3. Post-processing & Validators
        valid_ids: set[str] = set()
        for ev in evidence_items:
            valid_ids.add(ev.evidence_id)
        for t in turns:
            valid_ids.add(t.question_id)
        for c in candidate.claims:
            valid_ids.add(c.claim_id)

        validated_eval = validate_grounding(eval_result, valid_ids, all_answers_text)

        # 4. Scoring Engine
        has_followups = any(t.kind == "followup" for t in turns)
        components = calculate_component_scores(
            relevance_map=relevance_map,
            evidence_items=evidence_items,
            github_metrics=github_metrics,
            eval_result=validated_eval,
            has_followups=has_followups,
        )

        final_score, adjusted_weights = compute_score(
            components=components,
            weights=role.weights,
            sufficiency=sufficiency,
            sparse_factor=settings.SPARSE_FACTOR,
        )

        total_words = sum(t.answer_words for t in turns)
        avg_words = total_words // max(len(turns), 1)
        critical_assessed = len(validated_eval.per_question) >= 4

        confidence, conf_reason = determine_confidence(
            sufficiency=sufficiency,
            critical_assessed=critical_assessed,
            flags=validated_eval.flags,
            avg_words=avg_words,
        )

        band = determine_band(
            score=final_score,
            confidence=confidence,
            flags=validated_eval.flags,
            all_critical_assessed=critical_assessed,
            sufficiency=sufficiency,
        )

        inputs_hash = hash_scoring_inputs(components, adjusted_weights, sufficiency)

        # 5. Build Assembled Report
        report = build_readiness_report(
            candidate_id=candidate.candidate_id,
            role_id=role.role_id,
            role_title=role.title,
            display_name=candidate.display_name,
            band=band,
            confidence=confidence,
            confidence_reason=conf_reason,
            score=final_score,
            components=components,
            adjusted_weights=adjusted_weights,
            sufficiency=sufficiency,
            eval_result=validated_eval,
            evidence_items=evidence_items,
            timeline_obs=timeline_obs,
            notes=[{"author": n.author, "text": n.text, "is_override": n.is_override, "created_at": n.created_at.isoformat()} for n in candidate.notes],
        )

        # 6. Save Result
        db.query(Result).filter(Result.candidate_id == candidate_id).delete()
        res_row = Result(
            candidate_id=candidate.candidate_id,
            role_id=role.role_id,
            evaluation=validated_eval.model_dump(),
            component_scores=components,
            score=final_score,
            band=band,
            confidence=confidence,
            confidence_reason=conf_reason,
            flags=[f.model_dump() for f in validated_eval.flags],
            report=report.model_dump(),
            scoring_inputs_hash=inputs_hash,
        )
        db.add(res_row)

        candidate.status = "COMPLETED"
        session.state = "DONE"

        audit = Audit(
            entity_id=candidate.candidate_id,
            action="EVALUATION_COMPLETED",
            detail={"band": band, "confidence": confidence, "score": final_score},
        )
        db.add(audit)
        db.commit()

        logger.info(f"Evaluation pipeline completed for candidate {candidate_id}: {band} ({final_score}).")

    except Exception as exc:
        logger.exception(f"Unexpected error in evaluation pipeline for {candidate_id}: {exc}")
        if candidate:
            candidate.status = "EVALUATION_FAILED"
            db.commit()
    finally:
        db.close()
