import os, secrets
from pathlib import Path
from typing import Any

from pydantic import AnyHttpUrl, BaseSettings, EmailStr, PostgresDsn, validator
from fastapi.templating import Jinja2Templates  # like Environment from Jinja2


class Settings(BaseSettings):
    PROJECT_NAME: str = "TeachingSessionsPlanning"
    API_V1_STR: str = "/api/v1"  # urls start with /api/v1
    TEMPLATES_DIR: str = "app/templates"
    STATIC_DIR: str = "/static"
    SECRET_KEY: str = os.getenv("FASTAPI_SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # = 8 days
    SERVER_NAME: str = None
    SERVER_HOST: AnyHttpUrl = "http://127.0.0.1:8000"
    API_LINK: Path = Path(SERVER_HOST + API_V1_STR)
    API_DOCS_LINK: Path = Path(SERVER_HOST) / "docs"
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []
    USERS_OPEN_REGISTRATION: bool = True

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    POSTGRES_SERVER: str = None
    POSTGRES_USER: str = None
    POSTGRES_PASSWORD: str = None
    POSTGRES_DB: str = None
    POSTGRES_DATABASE_URI: str = "postgresql+asyncpg://postgres:postgres_key@localhost/p13_local_db"

    @validator("POSTGRES_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: str, values: dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    FIRST_SUPERUSER_FIRST_NAME = "admin first name"
    FIRST_SUPERUSER_LAST_NAME = "admin last name"
    FIRST_SUPERUSER_EMAIL: EmailStr = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "mysupersecretadminapikey"

    EMAIL_TEST_SPEAKER: EmailStr = "test_spk@example.com"  # type: ignore
    EMAIL_TEST_PARTICIPANT: EmailStr = "test_part@example.com"  # type: ignore

    PARTICIPANT_TYPES_NB_SESSION_WEEK: dict[str, int] = {"initial": 1, "continue": 2}
    PARTICIPANT_STATUS_DEFAULT_VALUE = "active"
    PARTICIPANT_STATUS: list[str] = [PARTICIPANT_STATUS_DEFAULT_VALUE, "break", "inactive"]

    SESSION_TYPES: list[str] = ["teach", "test"]
    SESSION_STATUS: list[str] = ["scheduled", "done", "unscheduled by participant",
                                 "unscheduled by speaker", "no-show"]

    SMTP_TLS: bool = True
    SMTP_LOCAL_PORT: int = 1025
    SMTP_SSL_PORT: int = 465
    START_TLS_PORT: int = 587
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_USER: str = None
    SMTP_PASSWORD: str = os.getenv("DEV_GMAIL_PWD")
    EMAILS_FROM_EMAIL: EmailStr = os.getenv("DEV_GMAIL_ADDRESS")

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 12
    EMAIL_TEMPLATES_DIR: Path = Path(TEMPLATES_DIR) / "email-templates/"
    EMAILS_ENABLED: bool = False

    @validator("EMAILS_ENABLED", pre=True)
    def get_emails_enabled(cls, v: bool, values: dict[str, Any]) -> bool:
        return bool(
            values.get("SMTP_HOST")
            and (values.get("SMTP_LOCAL_PORT") or values.get("START_TLS_PORT"))
            and values.get("EMAILS_FROM_EMAIL")
        )

    TESTS_EMAIL: EmailStr = os.getenv("DEV_GMAIL_ADDRESS")

    class Config:
        case_sensitive = True


settings = Settings()

jinja_templates = Jinja2Templates(directory=Path(settings.TEMPLATES_DIR))
