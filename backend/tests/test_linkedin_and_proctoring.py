import pytest
from app.config import settings
from app.services.linkedin_client import (
    LinkedInClient,
    clean_linkedin_url,
    extract_linkedin_username,
)
from app.services.web_fetch import SSRFSecurityError, validate_url_safety


def test_clean_linkedin_url_and_username():
    # Various valid inputs
    url1 = "https://www.linkedin.com/in/alexchen/"
    assert clean_linkedin_url(url1) == "https://www.linkedin.com/in/alexchen"
    assert extract_linkedin_username(url1) == "alexchen"

    url2 = "linkedin.com/in/jordan-lee-123"
    assert clean_linkedin_url(url2) == "https://linkedin.com/in/jordan-lee-123"
    assert extract_linkedin_username(url2) == "jordan-lee-123"

    url3 = "in/taylorswift"
    assert clean_linkedin_url(url3) == "https://www.linkedin.com/in/taylorswift"
    assert extract_linkedin_username(url3) == "taylorswift"

    url4 = "@morganreed"
    assert clean_linkedin_url(url4) == "https://www.linkedin.com/in/morganreed"
    assert extract_linkedin_username(url4) == "morganreed"


def test_linkedin_url_safety_ssrf():
    # Dangerous URLs must fail safety validation
    with pytest.raises(SSRFSecurityError):
        validate_url_safety("http://127.0.0.1/in/admin")

    with pytest.raises(SSRFSecurityError):
        validate_url_safety("http://169.254.169.254/latest/meta-data/")

    with pytest.raises(SSRFSecurityError):
        validate_url_safety("ftp://linkedin.com/in/alex")


def test_linkedin_client_authwall_fallback(respx_mock):
    # Mock LinkedIn returning 999 or 403 (common bot protection)
    client = LinkedInClient()
    respx_mock.get("https://www.linkedin.com/in/alexchen").respond(
        status_code=999,
        text="<html><body>Request Blocked</body></html>"
    )

    result = client.fetch_profile_evidence("https://www.linkedin.com/in/alexchen", candidate_id="c_test123")
    assert result["username"] == "alexchen"
    assert result["status"] == "authwall_fallback"
    assert "alexchen" in result["headline"]


def test_linkedin_client_successful_extraction(respx_mock):
    client = LinkedInClient()
    mock_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Alex Chen - Staff Backend Engineer - Stripe | LinkedIn</title>
        <meta property="og:title" content="Alex Chen - Staff Backend Engineer - Stripe">
        <meta property="og:description" content="Alex Chen is a Staff Backend Engineer at Stripe with 8+ years building distributed Python and Go microservices with PostgreSQL and Redis.">
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "Person",
          "name": "Alex Chen",
          "jobTitle": "Staff Backend Engineer",
          "worksFor": {"@type": "Organization", "name": "Stripe"}
        }
        </script>
    </head>
    <body>
        <h1>Alex Chen</h1>
        <p>Experienced distributed systems architect specializing in high-throughput payment gateways, Kafka, and Kubernetes.</p>
    </body>
    </html>
    """
    respx_mock.get("https://www.linkedin.com/in/alexchen").respond(
        status_code=200,
        text=mock_html
    )

    result = client.fetch_profile_evidence("https://www.linkedin.com/in/alexchen", candidate_id="c_test456")
    assert result["username"] == "alexchen"
    assert result["status"] == "extracted"
    assert "Staff Backend Engineer" in result["headline"]
    assert "Stripe" in result["summary"]
    assert "Stripe" in result["experiences"]
    assert "Python" in result["skills"] or "Go" in result["skills"] or "PostgreSQL" in result["skills"] or "Kafka" in result["skills"]


def test_proctoring_settings_and_api(client, db_session):
    from datetime import datetime, timedelta, timezone
    from app.models import Candidate, Role, Session as DBSession

    role = Role(title="ML Engineer", jd_text="Sample ML Job Description with sufficient length.")
    db_session.add(role)
    db_session.commit()

    cand = Candidate(
        role_id=role.role_id,
        display_name="Sarah Connor",
        linkedin_url="https://linkedin.com/in/sarahconnor",
        resume_path="dummy.pdf",
        status="READY",
    )
    db_session.add(cand)
    db_session.commit()

    plan = [{"question_id": "q1", "kind": "jd_scenario", "text": "Explain transformer attention."}]
    session = DBSession(
        candidate_id=cand.candidate_id,
        state="NOT_STARTED",
        question_plan=plan,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
        token_jti="test_proctor_token_789",
    )
    db_session.add(session)
    db_session.commit()

    # Query public assessment session endpoint
    resp = client.get("/api/v1/assessment/test_proctor_token_789")
    assert resp.status_code == 200
    data = resp.json()

    assert "proctoring" in data
    assert data["proctoring"]["enabled"] == settings.ENABLE_PROCTORING
    assert data["proctoring"]["disable_copy_paste"] == (settings.ENABLE_PROCTORING and settings.PROCTORING_DISABLE_COPY_PASTE)
    assert data["proctoring"]["track_tab_switch"] == (settings.ENABLE_PROCTORING and settings.PROCTORING_TRACK_TAB_SWITCH)
    assert data["question_index"] == 1
    assert data["total_planned"] == 1
