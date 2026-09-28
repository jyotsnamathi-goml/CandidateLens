import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from itsdangerous import BadTimeSignature, SignatureExpired, URLSafeTimedSerializer
from jose import JWTError, jwt

from app.config import settings

security = HTTPBearer()

link_serializer = URLSafeTimedSerializer(
    secret_key=settings.LINK_SIGNING_SECRET,
    salt="candidate-assessment-link"
)


def verify_hr_credentials(username: str, password: str) -> bool:
    """Constant-time comparison for HR credentials."""
    user_match = hmac.compare_digest(username.encode("utf-8"), settings.HR_USERNAME.encode("utf-8"))
    pass_match = hmac.compare_digest(password.encode("utf-8"), settings.HR_PASSWORD.encode("utf-8"))
    return user_match and pass_match


def create_jwt_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_TTL_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")


def get_current_hr_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate HR credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        username: str | None = payload.get("sub")
        if username is None or username != settings.HR_USERNAME:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception


def generate_candidate_token(candidate_id: str, session_jti: str) -> str:
    """Generate a signed expiring token for the candidate assessment."""
    payload = {
        "candidate_id": candidate_id,
        "jti": session_jti,
        "nonce": secrets.token_hex(8),
    }
    return link_serializer.dumps(payload)


def verify_candidate_token(token: str) -> dict:
    """Verify signed candidate token and return candidate_id and jti."""
    max_age_seconds = settings.ASSESSMENT_LINK_TTL_HOURS * 3600
    try:
        data = link_serializer.loads(token, max_age=max_age_seconds)
        return data
    except SignatureExpired:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Assessment link has expired."
        )
    except BadTimeSignature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid assessment link."
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed or invalid assessment token."
        )
