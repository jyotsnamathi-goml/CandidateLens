import pytest

from app.auth import generate_candidate_token, verify_candidate_token, verify_hr_credentials
from app.services.web_fetch import SSRFSecurityError, is_ip_disallowed, validate_url_safety


def test_ssrf_disallowed_ips():
    # Loopback
    assert is_ip_disallowed("127.0.0.1") is True
    assert is_ip_disallowed("127.0.0.2") is True
    assert is_ip_disallowed("::1") is True

    # Cloud metadata endpoint
    assert is_ip_disallowed("169.254.169.254") is True
    # Link local
    assert is_ip_disallowed("169.254.1.1") is True

    # Private IP blocks
    assert is_ip_disallowed("10.0.0.1") is True
    assert is_ip_disallowed("172.16.0.1") is True
    assert is_ip_disallowed("192.168.1.1") is True

    # Public safe IPs
    assert is_ip_disallowed("8.8.8.8") is False
    assert is_ip_disallowed("1.1.1.1") is False


def test_validate_url_safety_rejects_localhost_and_metadata():
    with pytest.raises(SSRFSecurityError):
        validate_url_safety("http://localhost:8000")

    with pytest.raises(SSRFSecurityError):
        validate_url_safety("http://127.0.0.1:8080")

    with pytest.raises(SSRFSecurityError):
        validate_url_safety("http://169.254.169.254/latest/meta-data/")

    with pytest.raises(SSRFSecurityError):
        validate_url_safety("ftp://example.com/file")


def test_constant_time_hr_auth():
    assert verify_hr_credentials("hr", "adminpassword123") is True
    assert verify_hr_credentials("wrong", "adminpassword123") is False
    assert verify_hr_credentials("hr", "wrongpassword") is False


def test_candidate_link_token_lifecycle():
    token = generate_candidate_token("c_test_01", "jti_test_123")
    assert isinstance(token, str)
    assert len(token) > 20

    data = verify_candidate_token(token)
    assert data["candidate_id"] == "c_test_01"
    assert data["jti"] == "jti_test_123"


def test_candidate_link_token_invalid():
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        verify_candidate_token("invalid-garbage-token-value")
