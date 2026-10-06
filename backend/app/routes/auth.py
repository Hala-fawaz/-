import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import TokenResponse, UserLogin, UserRegister, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

JWT_SECRET = os.getenv("JWT_SECRET", "risalah-dev-secret-change-before-production")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8")
    )


def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)

    payload = {
        "sub": str(user_id),
        "exp": expires_at
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )


@router.post("/register", response_model=UserResponse)
def register(request: UserRegister, db: Session = Depends(get_db)):
    email = request.email.strip().lower()

    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email.")

    if len(request.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters."
        )

    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered."
        )

    user = User(
        email=email,
        name=request.name.strip() or None,
        password_hash=hash_password(request.password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=TokenResponse)
def login(request: UserLogin, db: Session = Depends(get_db)):
    email = request.email.strip().lower()

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "email": user.email,
        "name": user.name
    }
