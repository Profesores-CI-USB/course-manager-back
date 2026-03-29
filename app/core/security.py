from datetime import datetime, timedelta, timezone
import uuid

import bcrypt as _bcrypt
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, status
import jwt
from jwt import InvalidTokenError

from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def _build_token(subject: str, token_type: str, expires_delta: timedelta) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    jti = str(uuid.uuid4())
    payload = {
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, jti


def create_access_token(subject: str) -> str:
    token, _ = _build_token(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return token


def create_refresh_token(subject: str) -> tuple[str, str]:
    return _build_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def create_password_reset_token(subject: str) -> str:
    token, _ = _build_token(
        subject=subject,
        token_type="password_reset",
        expires_delta=timedelta(minutes=settings.password_reset_token_expire_minutes),
    )
    return token


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        ) from exc


def _get_fernet() -> Fernet:
    if not settings.smtp_credentials_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falta SMTP_CREDENTIALS_KEY para cifrar credenciales SMTP",
        )
    try:
        return Fernet(settings.smtp_credentials_key.encode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SMTP_CREDENTIALS_KEY no tiene formato válido de Fernet",
        ) from exc


def encrypt_secret(secret: str) -> str:
    fernet = _get_fernet()
    return fernet.encrypt(secret.encode("utf-8")).decode("utf-8")


def decrypt_secret(secret_encrypted: str | None) -> str | None:
    if not secret_encrypted:
        return None
    fernet = _get_fernet()
    try:
        return fernet.decrypt(secret_encrypted.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No fue posible descifrar la contraseña SMTP almacenada",
        ) from exc
