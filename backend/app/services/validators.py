"""
Validators and Post-Processing Service:
- Grounding validator: drops findings or flags without valid references.
- Quote validator: verifies verbatim quotes in answers and caps unquoted scores at 2.
- Forbidden-language filter: neutralizes any accusatory phrasing.
"""

import re
from typing import Any

from app.schemas.llm import EvaluationResult, QuestionEvaluation

FORBIDDEN_WORDS = [
    r"\bdishonest\b",
    r"\bly(ing|ed)?\b",
    r"\bfake\b",
    r"\bfraud\b",
    r"\bcheat(ed|ing)?\b",
    r"\bplagiar\w*\b",
    r"\bdeceit\w*\b",
]

REPLACEMENTS = {
    "dishonest": "unverified",
    "lying": "potential claim gap",
    "lied": "stated without artifact support",
    "fake": "unverified artifact",
    "fraud": "unsubstantiated scope",
    "cheat": "divergent answer",
    "cheated": "divergent answer",
    "cheating": "divergent response pattern",
    "plagiarized": "closely matched public text",
    "plagiarism": "public text similarity",
}


def sanitize_forbidden_language(text: str) -> str:
    """Replace any accusatory words with neutral verification language."""
    sanitized = text
    for word, replacement in REPLACEMENTS.items():
        pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
        sanitized = pattern.sub(replacement, sanitized)

    # General fallback regex sweep
    for pat in FORBIDDEN_WORDS:
        sanitized = re.sub(pat, "unverified statement", sanitized, flags=re.IGNORECASE)

    return sanitized


def normalize_whitespace(text: str) -> str:
    return " ".join(text.lower().split())


def validate_quotes(
    evaluations: list[QuestionEvaluation],
    all_answers_text: str,
) -> list[QuestionEvaluation]:
    """
    Validate that every dimension score > 2 contains a verbatim quote from candidate answers.
    If quote is missing or not a substring, caps score at 2.
    """
    normalized_all_answers = normalize_whitespace(all_answers_text)

    for q_eval in evaluations:
        dimensions = [
            q_eval.technical_correctness,
            q_eval.technical_depth,
            q_eval.mechanism,
            q_eval.trade_offs,
            q_eval.problem_solving,
            q_eval.communication,
            q_eval.specificity,
        ]
        for dim in dimensions:
            if dim.score > 2:
                norm_quote = normalize_whitespace(dim.quote)
                if not norm_quote or (norm_quote not in normalized_all_answers):
                    dim.score = 2
                    dim.quote = f"[Unverified quote capped at 2]: {dim.quote}"

    return evaluations


def validate_grounding(
    eval_result: EvaluationResult,
    valid_ids: set[str],
    all_answers_text: str,
) -> EvaluationResult:
    """
    Drop any strength, gap, verification point, or flag ref that does not resolve
    to a valid evidence_id, claim_id, question_id, or an answer quote.
    """
    # 1. Sanitize text fields
    eval_result.consistency_rationale = sanitize_forbidden_language(eval_result.consistency_rationale)
    for probe_idx in range(len(eval_result.interview_probes)):
        eval_result.interview_probes[probe_idx] = sanitize_forbidden_language(eval_result.interview_probes[probe_idx])

    # 2. Filter findings (strengths, gaps, verification points)
    def filter_findings(findings: list[Any]) -> list[Any]:
        valid_findings = []
        for f in findings:
            clean_text = sanitize_forbidden_language(f.text)
            f.text = clean_text

            # Keep only references that exist in valid_ids or appear in answer text
            resolved_refs = [
                r for r in f.refs
                if r in valid_ids or normalize_whitespace(r) in normalize_whitespace(all_answers_text)
            ]
            if resolved_refs or not f.refs:
                f.refs = resolved_refs
                valid_findings.append(f)
        return valid_findings

    eval_result.strengths = filter_findings(eval_result.strengths)
    eval_result.gaps = filter_findings(eval_result.gaps)
    eval_result.verification_points = filter_findings(eval_result.verification_points)

    # 3. Filter flags
    valid_flags = []
    for fl in eval_result.flags:
        fl.action_text = sanitize_forbidden_language(fl.action_text)
        fl.public_evidence = sanitize_forbidden_language(fl.public_evidence or "")
        fl.candidate_statement = sanitize_forbidden_language(fl.candidate_statement or "")

        resolved_refs = [r for r in fl.refs if r in valid_ids]
        if resolved_refs:
            fl.refs = resolved_refs
            valid_flags.append(fl)

    eval_result.flags = valid_flags

    # Validate quotes in per_question
    eval_result.per_question = validate_quotes(eval_result.per_question, all_answers_text)

    return eval_result
