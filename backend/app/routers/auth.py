"""Registration, login, and current-user routes."""

import hmac

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.passwords import hash_password, verify_password
from app.auth.tokens import create_access_token
from app.dependencies import get_db
from app.config import get_settings
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, database: Session = Depends(get_db)) -> User:
    """Create a user account with a safely hashed password."""
    if payload.role == UserRole.COUNSELLOR:
        # Counsellor accounts grant access to every student's results, so they
        # cannot be self-provisioned without an out-of-band invite code.
        expected = get_settings().counsellor_invite_code
        supplied = payload.invite_code or ""
        if not expected or not hmac.compare_digest(supplied.encode(), expected.encode()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Counsellor registration requires a valid invite code",
            )
    email = str(payload.email).lower()
    if database.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")
    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    database.add(user)
    database.commit()
    database.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, database: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate credentials and issue a short-lived access token."""
    user = database.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=create_access_token(user))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user's profile."""
    return current_user
