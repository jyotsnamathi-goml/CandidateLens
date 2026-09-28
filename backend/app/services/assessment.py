"""
Assessment Session Engine.
Decides question sequence, serves prepared follow-ups based on lightweight deterministic heuristics,
and enforces hard turn and time caps.
"""

import re
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Session as DBSession
from app.models import Turn


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def is_answer_vague(answer_text: str, question: dict[str, Any], materials_text: str = "") -> bool:
    """
    Deterministic heuristics to detect vague or generic answers:
    1. Word count < VAGUE_ANSWER_MIN_WORDS (default 40).
    2. No digits and no first-person markers ('I', 'we', 'my', 'our').
    3. High token overlap with the question text itself (>60%).
    4. Simple 4-gram shingle overlap with candidate materials text (>75%).
    """
    words = count_words(answer_text)
    if words < settings.VAGUE_ANSWER_MIN_WORDS:
        return True

    lower_ans = answer_text.lower()

    # Check for first-person markers
    first_person = bool(re.search(r"\b(i|we|my|our|me|us)\b", lower_ans))
    has_digits = bool(re.search(r"\d", answer_text))

    if not first_person and not has_digits:
        return True

    # Overlap with question text
    q_words = set(re.findall(r"\b\w{4,}\b", question.get("text", "").lower()))
    ans_words = set(re.findall(r"\b\w{4,}\b", lower_ans))
    if q_words and ans_words:
        overlap = len(ans_words.intersection(q_words)) / len(ans_words)
        if overlap > 0.65:
            return True

    # Shingle overlap with candidate public materials (if provided)
    if materials_text and len(answer_text) > 80:
        ans_shingles = set([lower_ans[i : i + 25] for i in range(len(lower_ans) - 25)])
        mat_lower = materials_text.lower()
        if ans_shingles:
            matches = sum(1 for s in ans_shingles if s in mat_lower)
            if (matches / len(ans_shingles)) > 0.75:
                return True

    return False


def get_current_question_state(session: DBSession, db: Session) -> dict[str, Any]:
    """Calculate current turn, active question, and whether it's a follow-up."""
    turns = (
        db.query(Turn)
        .filter(Turn.session_id == session.session_id)
        .order_by(Turn.turn_no.asc())
        .all()
    )
    turn_count = len(turns)
    plan = session.question_plan or []

    # Map turns by question_id
    turns_by_q: dict[str, list[Turn]] = {}
    for t in turns:
        turns_by_q.setdefault(t.question_id, []).append(t)

    # Determine next planned question
    for idx, q in enumerate(plan):
        q_id = q.get("question_id")
        q_turns = turns_by_q.get(q_id, [])

        if not q_turns:
            # Not started yet
            return {
                "status": "active",
                "question": q,
                "is_followup": False,
                "turn_no": turn_count + 1,
            }
        elif len(q_turns) == 1:
            # Check if last turn triggered follow-up
            last_turn = q_turns[0]
            if last_turn.kind == "planned":
                # Check heuristics
                if is_answer_vague(last_turn.answer_text, q) and turn_count < settings.MAX_TURNS:
                    # Serve prepared follow-up
                    followup_text = q.get("follow_up_if_vague")
                    followup_q = dict(q)
                    followup_q["text"] = f"Follow-up: {followup_text}"
                    followup_q["is_followup"] = True
                    return {
                        "status": "active",
                        "question": followup_q,
                        "is_followup": True,
                        "turn_no": turn_count + 1,
                    }

    # All questions answered or turns exhausted
    return {
        "status": "completed",
        "question": None,
        "is_followup": False,
        "turn_no": turn_count,
    }
