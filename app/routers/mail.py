from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.models import User
from app.schemas.mail import SendMailRequest, SendMailResponse
from app.services.mail_service import get_smtp_config_for_user, send_email


router = APIRouter(prefix="/mail", tags=["mail"])


@router.post("/send", response_model=SendMailResponse)
async def send_mail(payload: SendMailRequest, current_user: User = Depends(get_current_user)):
    config = get_smtp_config_for_user(current_user)
    send_email(config=config, to_email=payload.to_email, subject=payload.subject, body=payload.body)
    return SendMailResponse(message="Correo enviado correctamente")
