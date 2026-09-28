from app.config import settings


def test_e2e_mock_pipeline_flow(client):
    """
    AC-1: End-to-end flow test:
    create role -> add candidate -> ingestion -> assessment link -> answer 6 questions -> evaluation -> report.
    Works in mock mode with no API key.
    """
    # 1. Login HR
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": settings.HR_USERNAME, "password": settings.HR_PASSWORD},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Role
    role_resp = client.post(
        "/api/v1/roles",
        headers=headers,
        json={
            "title": "Senior Distributed Backend Engineer",
            "jd_text": "We are seeking a senior engineer experienced in distributed systems, PostgreSQL, and high availability.",
            "role_family": "backend",
        },
    )
    assert role_resp.status_code == 201
    role_data = role_resp.json()
    role_id = role_data["role_id"]
    assert len(role_data["competencies"]) >= 4

    # 3. Add Candidate with simulated resume
    candidate_resp = client.post(
        f"/api/v1/roles/{role_id}/candidates",
        headers=headers,
        data={
            "display_name": "Taylor Swift",
            "consent": "true",
            "github_username": "taylorswift",
        },
        files={
            "resume": ("resume.txt", b"Senior Backend Engineer with 6 years experience in Python, PostgreSQL, and Redis.", "text/plain")
        },
    )
    assert candidate_resp.status_code == 201
    cand_data = candidate_resp.json()
    candidate_id = cand_data["candidate_id"]

    # Ingestion was scheduled in background. Let's run it directly or check status.
    from app.services.ingestion import run_candidate_ingestion
    run_candidate_ingestion(candidate_id)

    # Verify status is READY
    cand_get = client.get(f"/api/v1/candidates/{candidate_id}", headers=headers)
    assert cand_get.status_code == 200
    assert cand_get.json()["status"] == "READY"

    # 4. Generate Assessment Link
    link_resp = client.post(f"/api/v1/candidates/{candidate_id}/assessment-link", headers=headers)
    assert link_resp.status_code == 200
    assessment_token = link_resp.json()["token"]

    # 5. Candidate starts session
    session_resp = client.get(f"/api/v1/assessment/{assessment_token}")
    assert session_resp.status_code == 200
    sess_data = session_resp.json()
    assert sess_data["current_turn"] == 1
    assert sess_data["question"] is not None

    # 6. Candidate answers all 6 questions
    for i in range(6):
        ans_resp = client.post(
            f"/api/v1/assessment/{assessment_token}/answers",
            json={
                "answer_text": (
                    "In our architecture we enforce idempotency using Redis distributed locks and unique "
                    "transaction keys in PostgreSQL. We set a 3000ms TTL with 3 retries and handled failover "
                    "using monotonically increasing fencing tokens to prevent split brain."
                ),
                "time_taken_seconds": 60,
            },
        )
        assert ans_resp.status_code == 200
        step_data = ans_resp.json()
        if step_data["status"] == "completed":
            break

    # Run evaluation pipeline synchronously for the test
    from app.services.evaluation import run_evaluation_pipeline
    run_evaluation_pipeline(candidate_id)

    # 7. Check full Result
    result_resp = client.get(f"/api/v1/candidates/{candidate_id}/result", headers=headers)
    assert result_resp.status_code == 200
    result_data = result_resp.json()
    assert result_data["status"] == "COMPLETED"
    report = result_data["report"]
    assert report is not None
    assert report["band"] in ["Strong Readiness", "Moderate Readiness", "Needs Verification"]
    assert report["confidence"] in ["High", "Medium", "Low"]
    assert len(report["component_breakdown"]) == 7
    assert len(report["interview_probes"]) >= 2
    assert result_data["scoring_inputs_hash"] is not None
