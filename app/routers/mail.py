from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.exceptions import ForbiddenException
from app.deps import get_current_user
from app.models import User
from app.schemas.mail import SendMailRequest, SendMailResponse, TestMailRequest
from app.services.mail_service import get_smtp_config_for_user, markdown_to_html, send_email


router = APIRouter(prefix="/mail", tags=["mail"])


@router.post("/send", response_model=SendMailResponse)
async def send_mail(
    payload: SendMailRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> SendMailResponse:
    config = get_smtp_config_for_user(current_user)
    send_email(config=config, to_email=payload.to_email, subject=payload.subject, body=payload.body)
    return SendMailResponse(message="Correo enviado correctamente")


@router.post("/test", response_model=SendMailResponse)
async def test_mail(
    payload: TestMailRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> SendMailResponse:
    if settings.environment != "development":
        raise ForbiddenException("Este endpoint solo está disponible en entorno de desarrollo")

    if payload.content_type == "markdown":
        html_body = markdown_to_html(payload.body)
        plain_body = payload.body
    else:
        html_body = payload.body
        plain_body = payload.body

    config = get_smtp_config_for_user(current_user)
    send_email(
        config=config,
        to_email=payload.to_email,
        subject=payload.subject,
        body=plain_body,
        html_body=html_body,
    )
    return SendMailResponse(message="Correo de prueba enviado correctamente")
