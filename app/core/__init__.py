# Medical AI Assistant - Core Configuration
"""Application configuration and settings management."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Medical AI Assistant"
    APP_VERSION: str = "1.0.0"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/medical_ai.db"

    # Groq API
    GROQ_API_KEY: str = ""
    GROQ_MODEL_NAME: str = "llama-3.3-70b-versatile"
    GROQ_TEMPERATURE: float = 0.1
    GROQ_MAX_TOKENS: int = 2048

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/medical_ai.log"

    # Paths
    BASE_DIR: ClassVar[Path] = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: ClassVar[Path] = BASE_DIR / "data"
    LOGS_DIR: ClassVar[Path] = BASE_DIR / "logs"

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        """Initialize settings and create required directories."""
        super().__init__(**kwargs)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def database_path(self) -> str:
        """Get the SQLite database path from the URL."""
        return self.DATABASE_URL.replace("sqlite+aiosqlite:///", "")

    @property
    def is_groq_configured(self) -> bool:
        """Check if Groq API key is configured."""
        return bool(self.GROQ_API_KEY) and self.GROQ_API_KEY != "your_g...n"


# Global settings instance
settings = Settings()
