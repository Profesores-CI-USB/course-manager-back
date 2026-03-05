from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    project_name: str = Field(default="Course Manager Backend", validation_alias="PROJECT_NAME")
    api_v1_prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")
    frontend_url: str = Field(default="http://localhost:5173", validation_alias="FRONTEND_URL")

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")

    jwt_secret_key: str = Field(default="change-me-in-production", validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, validation_alias="REFRESH_TOKEN_EXPIRE_DAYS")
    password_reset_token_expire_minutes: int = Field(
        default=30,
        validation_alias="PASSWORD_RESET_TOKEN_EXPIRE_MINUTES",
    )

    smtp_host: str = Field(default="smtp.gmail.com", validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=587, validation_alias="SMTP_PORT")
    smtp_use_tls: bool = Field(default=True, validation_alias="SMTP_USE_TLS")
    mail_default_sender: str = Field(default="", validation_alias="MAIL_DEFAULT_SENDER")
    mail_default_password: str = Field(default="", validation_alias="MAIL_DEFAULT_PASSWORD")

    smtp_credentials_key: str = Field(default="", validation_alias="SMTP_CREDENTIALS_KEY")

    ai_model_name: str = Field(default="simple_nn", validation_alias="AI_MODEL_NAME")

    @field_validator("database_url", mode="before")
    @classmethod
    def ensure_async_database_url(cls, value: str) -> str:
        if not isinstance(value, str):
            return value

        normalized = value
        if normalized.startswith("postgres://"):
            normalized = normalized.replace("postgres://", "postgresql+asyncpg://", 1)
        elif normalized.startswith("postgresql://") and "+asyncpg" not in normalized:
            normalized = normalized.replace("postgresql://", "postgresql+asyncpg://", 1)

        if normalized.startswith("postgresql+asyncpg://"):
            parts = urlsplit(normalized)
            query_pairs = parse_qsl(parts.query, keep_blank_values=True)

            has_ssl = any(key == "ssl" for key, _ in query_pairs)
            rewritten_pairs = []
            for key, val in query_pairs:
                if key == "sslmode":
                    if not has_ssl:
                        rewritten_pairs.append(("ssl", val))
                    continue
                rewritten_pairs.append((key, val))

            normalized = urlunsplit(
                (parts.scheme, parts.netloc, parts.path, urlencode(rewritten_pairs, doseq=True), parts.fragment)
            )

        return normalized


settings = Settings()
