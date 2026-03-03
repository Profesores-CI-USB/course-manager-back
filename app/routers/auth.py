from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db, get_redis
from app.models import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
)
from app.schemas.user import UserOut


router = APIRouter(prefix="/auth", tags=["auth"])


def to_user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        smtp_configured=bool(user.smtp_email and user.smtp_password_encrypted),
        created_at=user.created_at,
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    exists = await db.execute(select(User).where(User.email == payload.email))
    if exists.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El correo ya está registrado")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return to_user_out(user)


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    query = await db.execute(select(User).where(User.email == payload.email))
    user = query.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    access_token = create_access_token(str(user.id))
    refresh_token, refresh_jti = create_refresh_token(str(user.id))

    ttl = int(timedelta(days=settings.refresh_token_expire_days).total_seconds())
    await redis.setex(f"refresh:{refresh_jti}", ttl, str(user.id))

    return AuthResponse(
        user=to_user_out(user),
        tokens=TokenPair(access_token=access_token, refresh_token=refresh_token),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh_tokens(payload: RefreshRequest, redis=Depends(get_redis)):
    token_payload = decode_token(payload.refresh_token)
    if token_payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")

    subject = token_payload.get("sub")
    old_jti = token_payload.get("jti")
    if not subject or not old_jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")

    key = f"refresh:{old_jti}"
    exists = await redis.exists(key)
    if not exists:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revocado")

    await redis.delete(key)

    access_token = create_access_token(subject)
    refresh_token, refresh_jti = create_refresh_token(subject)
    ttl = int(timedelta(days=settings.refresh_token_expire_days).total_seconds())
    await redis.setex(f"refresh:{refresh_jti}", ttl, subject)

    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
async def logout(payload: LogoutRequest, redis=Depends(get_redis)):
    token_payload = decode_token(payload.refresh_token)
    if token_payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")

    jti = token_payload.get("jti")
    if jti:
        await redis.delete(f"refresh:{jti}")

    return {"message": "Sesión cerrada"}
