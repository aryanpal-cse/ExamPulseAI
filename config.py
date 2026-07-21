"""
ExamPulse AI - Configuration
=============================
All configuration is driven by environment variables so the app can run
identically on local SQLite, Render + Neon Postgres, or CI test runners.

IMPORTANT: The app must run correctly with GEMINI_API_KEY and
HUGGINGFACE_API_KEY left EMPTY. Those keys only unlock optional
generative-AI wording enhancements (see services/ai/mentor_llm.py in a
later phase) — they must never gate core analytics, predictions, or
recommendations.
"""

import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


def _bool_env(key: str, default: bool = False) -> bool:
    val = os.environ.get(key)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


class BaseConfig:
    """Shared configuration across all environments."""

    # --- Core / security ---------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    WTF_CSRF_ENABLED = True

    # --- Database ------------------------------------------------------------
    # Falls back to a local SQLite file when DATABASE_URL is not set, so the
    # app runs out-of-the-box with zero external services configured.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'data', 'exampulse.db')}"
    )
    # Render/Neon sometimes hand out `postgres://` URLs; SQLAlchemy 1.4+/2.x
    # requires `postgresql://`.
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            "postgres://", "postgresql://", 1
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    # --- Sessions / auth -----------------------------------------------------
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # --- File uploads ----------------------------------------------------------
    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER", os.path.join(basedir, "data", "uploads")
    )
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_MB", "20")) * 1024 * 1024  # 20 MB default
    ALLOWED_UPLOAD_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

    # --- Optional AI enhancement layer (LEVEL 3 in the fallback hierarchy) ---
    # These are intentionally allowed to be empty strings / None. Every
    # service that touches them MUST check `AI_ENHANCEMENTS_ENABLED` (or the
    # individual key) and gracefully fall back to Level 1 (deterministic
    # rules) or Level 2 (local NLP/ML) when unset or when the call fails.
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
    HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY", "").strip()

    @property
    def AI_ENHANCEMENTS_ENABLED(self) -> bool:  # noqa: N802 (kept as constant-style name)
        return bool(self.GEMINI_API_KEY or self.HUGGINGFACE_API_KEY)

    # --- App-level constants -------------------------------------------------
    APP_NAME = "ExamPulse AI"
    APP_TAGLINE = "Analyze. Prepare. Practice. Improve."
    PAGINATION_PER_PAGE = 20


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_ECHO = _bool_env("SQL_ECHO", False)


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    def __init__(self):
        # Fail loudly in production if SECRET_KEY was left at the dev default.
        if self.SECRET_KEY == "dev-secret-key-change-me":
            raise RuntimeError(
                "SECRET_KEY must be set via environment variable in production."
            )


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(env_name: str | None = None):
    env_name = env_name or os.environ.get("FLASK_ENV", "development")
    return config_by_name.get(env_name, DevelopmentConfig)
