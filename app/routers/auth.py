from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, get_redis
from app.deps import get_current_user
from app.models import User
from app.schemas.auth import (
    AuthResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenPair,
)
from app.schemas.user import UserOut
from app.services import auth_service


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await auth_service.create_user(db=db, current_user=current_user, payload=payload)


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    return await auth_service.login(db=db, redis=redis, payload=payload)


@router.post("/refresh", response_model=TokenPair)
async def refresh_tokens(payload: RefreshRequest, redis=Depends(get_redis)):
    return await auth_service.refresh_tokens(redis=redis, payload=payload)


@router.post("/logout")
async def logout(payload: LogoutRequest, redis=Depends(get_redis)):
    return await auth_service.logout(redis=redis, payload=payload)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.forgot_password(db=db, payload=payload)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.reset_password(db=db, payload=payload)


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    payload: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await auth_service.change_password(db=db, current_user=current_user, payload=payload)
