from datetime import timedelta

from fastapi import APIRouter, HTTPException, status

from app.auth import create_jwt_token, verify_hr_credentials
from app.config import settings
from app.schemas.api import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    if not verify_hr_credentials(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    expires = timedelta(minutes=settings.JWT_TTL_MINUTES)
    token = create_jwt_token({"sub": payload.username}, expires_delta=expires)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.JWT_TTL_MINUTES * 60,
    )
