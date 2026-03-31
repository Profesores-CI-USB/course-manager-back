import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from app.core.config import settings
from app.core.exceptions import BadGatewayException, BadRequestException
from app.core.security import decrypt_secret
from app.models import User


@dataclass
class SMTPConfig:
    host: str
    port: int
    use_tls: bool
    username: str
    password: str
    from_email: str


def get_smtp_config_for_user(user: User) -> SMTPConfig:
    if user.smtp_email and user.smtp_password_encrypted:
        password = decrypt_secret(user.smtp_password_encrypted)
        if not password:
            raise BadRequestException("Credenciales SMTP del usuario incompletas")

        return SMTPConfig(
            host=settings.smtp_host,
            port=settings.smtp_port,
            use_tls=settings.smtp_use_tls,
            username=user.smtp_email,
            password=password,
            from_email=user.smtp_email,
        )

    if not settings.mail_default_sender or not settings.mail_default_password:
        raise BadRequestException("No hay SMTP por usuario ni SMTP global configurado")

    return SMTPConfig(
        host=settings.smtp_host,
        port=settings.smtp_port,
        use_tls=settings.smtp_use_tls,
        username=settings.mail_default_sender,
        password=settings.mail_default_password,
        from_email=settings.mail_default_sender,
    )


def send_email(config: SMTPConfig, to_email: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = config.from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(config.host, config.port, timeout=20) as server:
            if config.use_tls:
                server.starttls()
            server.login(config.username, config.password)
            server.send_message(message)
    except smtplib.SMTPException as exc:
        raise BadGatewayException(f"Error enviando correo SMTP: {exc}") from exc
