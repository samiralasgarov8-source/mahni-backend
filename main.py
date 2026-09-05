"""
SECTION 7: BACKEND KURULUŞU — FastAPI tətbiqinin giriş nöqtəsi.

Lokal işə salmaq:
    cd backend
    python -m venv venv && source venv/bin/activate   # Windows: venv\\Scripts\\activate
    pip install -r requirements.txt
    cp .env.example .env   # sonra açarlarını doldur (hamısı boş qala bilər, demo rejimi işləyər)
    uvicorn app.main:app --reload --port 8000

Sonra brauzerdə: http://localhost:8000/docs (Swagger UI, bütün endpoint-ləri canlı test etmək üçün)

Render-ə deploy: README_DEPLOY.md-yə bax.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .database import init_db
from .routers import content, images, tts, video, youtube, analytics

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Auto Video Generator — mövzu -> mətn -> tərcümə -> şəkil -> səs -> video -> YouTube -> analitika",
    version="1.0.0",
)

# CORS: frontend HTML fərqli domendən/portdan çağırırsa lazımdır
allowed_origins = (
    ["*"] if settings.ALLOWED_ORIGINS == "*" else [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Generasiya olunan video/audio fayllarını ictimai et (/media/... yolu ilə)
os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.MEDIA_ROOT), name="media")

app.include_router(content.router)
app.include_router(images.router)
app.include_router(tts.router)
app.include_router(video.router)
app.include_router(youtube.router)
app.include_router(analytics.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.ENV,
        "docs": "/docs",
    }


@app.get("/health")
def health():
    """Render.com kimi hosting platformaları bu endpoint ilə tətbiqin canlı olduğunu yoxlayır."""
    return {"status": "healthy"}
