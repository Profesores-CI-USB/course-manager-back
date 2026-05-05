from typing import Literal

from pydantic import BaseModel, EmailStr


class SendMailRequest(BaseModel):
    to_email: EmailStr
    subject: str
    body: str


class TestMailRequest(BaseModel):
    to_email: EmailStr
    subject: str
    body: str
    content_type: Literal["markdown", "html"] = "markdown"


class SendMailResponse(BaseModel):
    message: str
