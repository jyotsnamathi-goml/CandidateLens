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
