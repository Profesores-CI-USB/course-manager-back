from datetime import timedelta
from urllib.parse import quote
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
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
from app.services.common import _is_admin
from app.services.mail_service import SMTPConfig, send_email


def _get_recovery_smtp_config() -> SMTPConfig:
    if not settings.mail_default_sender or not settings.mail_default_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SMTP global no configurado para recuperación de contraseña",
        )

    return SMTPConfig(
        host=settings.smtp_host,
        port=settings.smtp_port,
        use_tls=settings.smtp_use_tls,
        username=settings.mail_default_sender,
        password=settings.mail_default_password,
        from_email=settings.mail_default_sender,
    )


def _to_user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        smtp_configured=bool(user.smtp_email and user.smtp_password_encrypted),
        created_at=user.created_at,
    )


async def create_user(db: AsyncSession, current_user: User, payload: RegisterRequest) -> UserOut:
    if not _is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un admin puede crear usuarios",
        )

    exists = await db.execute(select(User).where(User.email == payload.email))
    if exists.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El correo ya está registrado")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _to_user_out(user)


async def login(db: AsyncSession, redis, payload: LoginRequest) -> AuthResponse:
    query = await db.execute(select(User).where(User.email == payload.email))
    user = query.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    access_token = create_access_token(str(user.id))
    refresh_token, refresh_jti = create_refresh_token(str(user.id))

    ttl = int(timedelta(days=settings.refresh_token_expire_days).total_seconds())
    await redis.setex(f"refresh:{refresh_jti}", ttl, str(user.id))

    return AuthResponse(
        user=_to_user_out(user),
        tokens=TokenPair(access_token=access_token, refresh_token=refresh_token),
    )


async def refresh_tokens(redis, payload: RefreshRequest) -> TokenPair:
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


async def logout(redis, payload: LogoutRequest) -> dict[str, str]:
    token_payload = decode_token(payload.refresh_token)
    if token_payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")

    jti = token_payload.get("jti")
    if jti:
        await redis.delete(f"refresh:{jti}")

    return {"message": "Sesión cerrada"}


async def forgot_password(db: AsyncSession, payload: ForgotPasswordRequest) -> MessageResponse:
    message = "Si el correo existe, se enviaron instrucciones para recuperar la contraseña"

    query = await db.execute(select(User).where(User.email == payload.email))
    user = query.scalar_one_or_none()
    if user is None:
        return MessageResponse(message=message)

    token = create_password_reset_token(str(user.id))
    reset_link = f"{settings.frontend_url.rstrip('/')}/reset-password?token={quote(token, safe='')}"
    email_body = (
        "Hola,\n\n"
        "Recibimos una solicitud para restablecer tu contraseña.\n"
        f"Usa este enlace para cambiar tu contraseña: {reset_link}\n\n"
        f"Si lo necesitas manualmente, tu token es: {token}\n\n"
        "Si no solicitaste este cambio, ignora este mensaje."
    )
    smtp_config = _get_recovery_smtp_config()
    send_email(
        smtp_config,
        to_email=user.email,
        subject="Recuperación de contraseña",
        body=email_body,
    )

    return MessageResponse(message=message)


async def reset_password(db: AsyncSession, payload: ResetPasswordRequest) -> MessageResponse:
    token_payload = decode_token(payload.token)
    if token_payload.get("type") != "password_reset":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de recuperación inválido")

    subject = token_payload.get("sub")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de recuperación inválido")

    try:
        user_id = UUID(subject)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de recuperación inválido") from exc

    query = await db.execute(select(User).where(User.id == user_id))
    user = query.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    user.hashed_password = hash_password(payload.new_password)
    db.add(user)
    await db.commit()

    return MessageResponse(message="Contraseña actualizada correctamente")


async def change_password(db: AsyncSession, current_user: User, payload: ChangePasswordRequest) -> MessageResponse:
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Contraseña actual inválida")

    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe ser diferente a la actual",
        )

    current_user.hashed_password = hash_password(payload.new_password)
    db.add(current_user)
    await db.commit()

    return MessageResponse(message="Contraseña actualizada correctamente")
