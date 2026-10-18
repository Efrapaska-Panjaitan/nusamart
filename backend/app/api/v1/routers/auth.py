from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.models.commerce import Cart
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(409, "Email sudah terdaftar")
    user = User(email=email, full_name=payload.full_name.strip(), password_hash=hash_password(payload.password), role="customer")
    db.add(user)
    try:
        db.flush()
        db.add(Cart(user_id=user.id))
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Email sudah terdaftar") from exc
    return user

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Email atau password salah")
    if not user.is_active:
        raise HTTPException(403, "Akun tidak aktif")
    settings = get_settings()
    return TokenResponse(access_token=create_access_token(user.id, user.role), expires_in=settings.access_token_expire_minutes * 60, user=UserResponse.model_validate(user))

@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user
