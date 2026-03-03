from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import encrypt_secret
from app.db.session import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas.user import SmtpCredentialsUpdate, UserOut, UserSmtpOut


router = APIRouter(prefix="/users", tags=["users"])


def to_user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        smtp_configured=bool(user.smtp_email and user.smtp_password_encrypted),
        created_at=user.created_at,
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return to_user_out(current_user)


@router.get("/me/smtp", response_model=UserSmtpOut)
async def get_my_smtp(current_user: User = Depends(get_current_user)):
    return UserSmtpOut(
        smtp_email=current_user.smtp_email,
        has_password=bool(current_user.smtp_password_encrypted),
    )


@router.put("/me/smtp", response_model=UserSmtpOut)
async def upsert_my_smtp(
    payload: SmtpCredentialsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.smtp_email = payload.smtp_email
    current_user.smtp_password_encrypted = encrypt_secret(payload.smtp_password)

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    return UserSmtpOut(
        smtp_email=current_user.smtp_email,
        has_password=bool(current_user.smtp_password_encrypted),
    )
