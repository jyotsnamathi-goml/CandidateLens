from app.services.assessment import count_words, is_answer_vague


def test_count_words():
    assert count_words("Hello world, this is a test.") == 6
    assert count_words("") == 0


def test_is_answer_vague_short_length():
    # Fewer than 40 words should trigger vague heuristic
    short_answer = "I would just use Redis locks to make sure only one request runs at a time."
    q = {"text": "How do you guarantee idempotency in payment webhooks?"}
    assert is_answer_vague(short_answer, q) is True


def test_is_answer_vague_generic_no_pronouns_or_digits():
    # Long answer (>40 words) but purely textbook generic with no first-person pronouns and no digits
    generic_text = (
        "Idempotency in distributed computing is achieved by creating unique keys for each operation. "
        "The system stores these keys in a database table. When another request arrives, the system "
        "checks if the key exists. If the key exists, the request returns immediately without "
        "re-processing the operation. This avoids duplicate state modifications."
    )
    q = {"text": "How do you guarantee idempotency in payment webhooks?"}
    assert is_answer_vague(generic_text, q) is True


def test_is_answer_specific_passes():
    # Specific answer with 'I', 'we', digits, and concrete parameters
    specific_text = (
        "In our payment architecture, we enforce idempotency by storing a 64-character hash of the "
        "webhook payload into PostgreSQL within an ACID transaction. We set a 3000ms Redis lock with "
        "3 retry attempts. If Stripe times out after 500ms, our worker marks the order state as "
        "PENDING_CONFIRMATION rather than double charging."
    )
    q = {"text": "How do you guarantee idempotency in payment webhooks?"}
    assert is_answer_vague(specific_text, q) is False


def test_question_count_does_not_increase_on_follow_up(db_session):
    from datetime import datetime, timedelta, timezone
    from app.models import Candidate, Role, Session as DBSession, Turn
    from app.services.assessment import get_current_question_state

    # Create dummy role and candidate
    role = Role(title="Backend Engineer", jd_text="Sample JD with 40+ chars for testing purposes.")
    db_session.add(role)
    db_session.commit()

    cand = Candidate(
        role_id=role.role_id,
        display_name="Test Dev",
        resume_path="dummy.pdf",
        status="IN_ASSESSMENT",
    )
    db_session.add(cand)
    db_session.commit()

    plan = [
        {
            "question_id": "q1",
            "kind": "jd_scenario",
            "text": "Explain distributed transaction handling.",
            "follow_up_if_vague": "Which isolation level did you use?",
        },
        {
            "question_id": "q2",
            "kind": "jd_scenario",
            "text": "How do you handle schema migrations without downtime?",
            "follow_up_if_vague": "What command avoids locking?",
        },
    ]

    session = DBSession(
        candidate_id=cand.candidate_id,
        state="ACTIVE",
        question_plan=plan,
        turn_count=0,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        token_jti="test_jti_123",
    )
    db_session.add(session)
    db_session.commit()

    # Turn 0: Question 1 initial state
    state1 = get_current_question_state(session, db_session)
    assert state1["is_followup"] is False
    assert state1["question_index"] == 1
    assert state1["turn_no"] == 1
    assert state1["question"]["question_id"] == "q1"

    # Submit vague answer for Question 1
    turn1 = Turn(
        session_id=session.session_id,
        turn_no=1,
        question_id="q1",
        kind="planned",
        question_text="Explain distributed transaction handling.",
        answer_text="I used transactions and locks.",
        answer_words=5,
        time_taken_seconds=20,
    )
    db_session.add(turn1)
    session.turn_count = 1
    db_session.commit()

    # Follow-up triggered for Question 1: question_index MUST remain 1!
    state2 = get_current_question_state(session, db_session)
    assert state2["is_followup"] is True
    assert state2["question_index"] == 1
    assert state2["turn_no"] == 2
    assert "Follow-up:" in state2["question"]["text"]

    # Submit answer for the follow-up
    turn2 = Turn(
        session_id=session.session_id,
        turn_no=2,
        question_id="q1",
        kind="followup",
        question_text=state2["question"]["text"],
        answer_text="We used SERIALIZABLE isolation in PostgreSQL with 3 retry loops on serialization failure 40001.",
        answer_words=15,
        time_taken_seconds=30,
    )
    db_session.add(turn2)
    session.turn_count = 2
    db_session.commit()

    # Move to Question 2: question_index is now 2 (out of 2)!
    state3 = get_current_question_state(session, db_session)
    assert state3["is_followup"] is False
    assert state3["question_index"] == 2
    assert state3["turn_no"] == 3
    assert state3["question"]["question_id"] == "q2"

