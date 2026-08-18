import os
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Cyanki API"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./cyanki.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey-dev-only")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Email (password recovery)
    MAIL_SERVER: str = os.getenv("SERVER_MAIL_SERVER", "")
    MAIL_PORT: int = int(os.getenv("SERVER_MAIL_PORT", "465"))
    MAIL_USER: str = os.getenv("SERVER_MAIL_USER", "")
    MAIL_PASSWORD: str = os.getenv("SERVER_MAIL_PASSWORD", "")
    MAIL_SENDER: str = os.getenv("SERVER_MAIL_SENDER", "")
    MAIL_USE_SSL: bool = os.getenv("SERVER_HTTPS", "false").lower() == "true"

    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5174")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # CORS: origens extras separadas por virgula, ex.:
    # CORS_ORIGINS=https://cyanki.exemplo.com,https://www.cyanki.exemplo.com
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "")

    # Origens liberadas em desenvolvimento (dev server e preview do SvelteKit)
    _DEV_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3015",
        "http://127.0.0.1:3015",
    ]

    @property
    def cors_origins(self) -> List[str]:
        """Origens do CORS: FRONTEND_URL + CORS_ORIGINS, mais localhost fora de producao."""
        origins = [o.strip().rstrip("/") for o in self.CORS_ORIGINS.split(",") if o.strip()]
        if self.FRONTEND_URL:
            origins.append(self.FRONTEND_URL.strip().rstrip("/"))
        if self.ENVIRONMENT != "production":
            origins.extend(self._DEV_ORIGINS)
        return sorted(set(origins))

settings = Settings()
