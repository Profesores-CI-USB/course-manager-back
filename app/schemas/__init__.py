from app.schemas.ai import AIPredictRequest, AIPredictResponse
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
from app.schemas.mail import SendMailRequest, SendMailResponse
from app.schemas.user import SmtpCredentialsUpdate, UserOut, UserSmtpOut

__all__ = [
    "AIPredictRequest",
    "AIPredictResponse",
    "AuthResponse",
    "ChangePasswordRequest",
    "ForgotPasswordRequest",
    "LoginRequest",
    "LogoutRequest",
    "MessageResponse",
    "RefreshRequest",
    "RegisterRequest",
    "ResetPasswordRequest",
    "TokenPair",
    "SendMailRequest",
    "SendMailResponse",
    "SmtpCredentialsUpdate",
    "UserOut",
    "UserSmtpOut",
]
