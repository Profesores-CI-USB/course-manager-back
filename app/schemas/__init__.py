from app.schemas.ai import AIPredictRequest, AIPredictResponse
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
)
from app.schemas.mail import SendMailRequest, SendMailResponse
from app.schemas.user import SmtpCredentialsUpdate, UserOut, UserSmtpOut

__all__ = [
    "AIPredictRequest",
    "AIPredictResponse",
    "AuthResponse",
    "LoginRequest",
    "LogoutRequest",
    "RefreshRequest",
    "RegisterRequest",
    "TokenPair",
    "SendMailRequest",
    "SendMailResponse",
    "SmtpCredentialsUpdate",
    "UserOut",
    "UserSmtpOut",
]
