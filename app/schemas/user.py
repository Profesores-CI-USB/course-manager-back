from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None
    role: Literal["admin", "professor"]
    smtp_configured: bool
    created_at: datetime


class SmtpCredentialsUpdate(BaseModel):
    smtp_email: EmailStr
    smtp_password: str


class UserSmtpOut(BaseModel):
    smtp_email: EmailStr | None
    has_password: bool
