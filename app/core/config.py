import sys
from pathlib import Path

from loguru import logger
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE_PATH = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """
    Settings of FastAPI SHA256 application
    """

    # ── App ───────────────────────────────────────────
    APP_NAME: str = "FastAPI SHA256"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    # ── Database parts ────────────────────────────────
    DATABASE_URL: str | None = Field(
        default=None,
        examples=["postgresql+asyncpg://user:pass@host:5432/dbname"],
    )
    DB_USER: str | None = Field(default=None, examples=["postgres"])
    DB_PASSWORD: str | None = Field(default=None, examples=["secret"])
    DB_HOST: str | None = Field(default=None, examples=["postgres"])
    DB_PORT: int | None = Field(default=None, examples=[5432])
    DB_NAME: str | None = Field(default=None, examples=["fastapi_sha256_db"])

    @classmethod
    @field_validator(
        "ENVIRONMENT",
        "DATABASE_URL",
        "DB_USER",
        "DB_PASSWORD",
        "DB_HOST",
        "DB_NAME",
        "EXTERNAL_SECRET_KEY",
        "JWT_SECRET_KEY",
        mode="before",
    )
    def strip_quotes(cls, value):
        """Remove wrapping quotes from string values loaded from environment."""
        if isinstance(value, str):
            return value.strip().strip('"').strip("'")
        return value

    @classmethod
    @field_validator("DEBUG", "DB_PORT", mode="before")
    def strip_scalar_quotes(cls, value):
        """Remove wrapping quotes before Pydantic parses bool and int settings."""
        if isinstance(value, str):
            value = value.strip().strip('"').strip("'")
        return value

    @model_validator(mode="after")
    def validate_database_settings(self):
        """Ensure database connection settings are complete."""
        if self.DATABASE_URL:
            return self

        missing = [
            name
            for name in ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME")
            if not getattr(self, name)
        ]
        if missing:
            raise ValueError(
                "Missing database settings: "
                + ", ".join(missing)
                + ". Provide DATABASE_URL or all DB_* variables."
            )
        return self

    @property
    def database_url(self) -> str:
        """Build SQLAlchemy async database URL from settings."""
        if self.DATABASE_URL:
            return self.DATABASE_URL

        missing = [
            name
            for name in ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME")
            if not getattr(self, name)
        ]
        if missing:
            raise ValueError(
                "Missing database settings: "
                + ", ".join(missing)
                + ". Provide DATABASE_URL or all DB_* variables."
            )

        return (
            f"postgresql+asyncpg://"
            f"{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # ── Security ──────────────────────────────────────
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    EXTERNAL_SECRET_KEY: str

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        case_sensitive=False,
        extra="ignore",
    )


class LoguruConfig:
    def __init__(self):
        """Create the runtime log directory if it does not exist."""
        self.LOG_DIR = PROJECT_ROOT / "logs"
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)

    def setup_logging(self) -> None:
        """Configure stdout, application, and error log sinks."""
        logger.remove()  # before new setup any other loggers must be removed

        # ── STDOUT (for docker / uvicorn) ────────────────────────────
        logger.add(
            sys.stdout,
            level="INFO",
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "{message} | {extra}"
            ),
            enqueue=True,  # safe logging for async and multiprocess functions
        )

        # ── INFO log ─────────────────────────────────────────────────
        logger.add(
            self.LOG_DIR / "app.log",
            level="INFO",
            rotation="10 MB",
            retention="14 days",
            compression="zip",
            enqueue=True,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level} | {name}:{function}:{line} | "
                "{message} | {extra}"
            ),
        )

        # ── ERROR log ────────────────────────────────────────────────
        logger.add(
            self.LOG_DIR / "error.log",
            mode="a",
            level="ERROR",
            rotation="5 MB",
            retention="30 days",
            compression="zip",
            enqueue=True,
            backtrace=True,
            diagnose=False,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level} | {name}:{function}:{line} | "
                "{message} | {extra}"
            ),
        )


settings = Settings()
loguru_config_obj = LoguruConfig()
