from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    project_name: str = Field(default="Course Manager Backend", validation_alias="PROJECT_NAME")
    api_v1_prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")

    jwt_secret_key: str = Field(default="change-me-in-production", validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, validation_alias="REFRESH_TOKEN_EXPIRE_DAYS")

    smtp_host: str = Field(default="smtp.gmail.com", validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=587, validation_alias="SMTP_PORT")
    smtp_use_tls: bool = Field(default=True, validation_alias="SMTP_USE_TLS")
    mail_default_sender: str = Field(default="", validation_alias="MAIL_DEFAULT_SENDER")
    mail_default_password: str = Field(default="", validation_alias="MAIL_DEFAULT_PASSWORD")

    smtp_credentials_key: str = Field(default="", validation_alias="SMTP_CREDENTIALS_KEY")

    ai_model_name: str = Field(default="simple_nn", validation_alias="AI_MODEL_NAME")


settings = Settings()
