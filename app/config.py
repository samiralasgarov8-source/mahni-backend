"""
SECTION 7: BACKEND KURULUŞU
Konfiqurasiya — bütün gizli açarlar / URL-lər burada, .env faylından oxunur.
Heç vaxt açarları koda hardcode etmə — .env.example-a bax.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Ümumi ---
    APP_NAME: str = "Auto Video Generator API"
    ENV: str = "development"  # development | production
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = "*"  # CORS üçün, produksiyada domenini yaz: "https://sən-domenin.com"

    # --- Verilənlər bazası ---
    # Render-də Postgres üçün: postgresql://user:pass@host/dbname
    # Lokal test üçün default: sqlite (fayl əsaslı, quraşdırma tələb etmir)
    DATABASE_URL: str = "sqlite:///./app.db"

    # --- YouTube Data API + Analytics API + OAuth ---
    YOUTUBE_API_KEY: str = ""          # Google Cloud Console -> API Key (public data üçün)
    GOOGLE_CLIENT_ID: str = ""         # OAuth 2.0 Client ID (upload + analytics üçün)
    GOOGLE_CLIENT_SECRET: str = ""     # OAuth 2.0 Client Secret
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/youtube/callback"

    # --- AdSense API ---
    ADSENSE_ACCOUNT_ID: str = ""       # məs: pub-1234567890123456

    # --- Şəkil mənbəyi (SECTION 2) ---
    PEXELS_API_KEY: str = ""

    # --- TTS (SECTION 3) ---
    TTS_PROVIDER: str = "gtts"         # gtts (pulsuz) | elevenlabs | azure
    ELEVENLABS_API_KEY: str = ""
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = ""

    # --- Tərcümə (SECTION 1) ---
    TRANSLATE_PROVIDER: str = "deep_translator"  # pulsuz, açar tələb etmir

    # --- Fayl saxlama ---
    MEDIA_ROOT: str = "./media"        # generasiya olunan video/audio buradadır
    PUBLIC_BASE_URL: str = "http://localhost:8000"  # media fayllarına tam URL üçün prefiks

    # --- Fon tapşırıq / queue (video render vaxt alır) ---
    USE_BACKGROUND_TASKS: bool = True


@lru_cache
def get_settings() -> "Settings":
    return Settings()
