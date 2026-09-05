"""SECTION 7: SECTION 5-in API endpoint-ləri (kanal idarəetməsi + YouTube-a yükləmə + OAuth)."""
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import requests

from .. import schemas, models
from ..config import get_settings
from ..database import get_db
from ..services import youtube_service

router = APIRouter(prefix="/api", tags=["youtube"])
settings = get_settings()


# ---------- Kanal CRUD ----------
@router.get("/channels", response_model=list[schemas.ChannelOut])
def list_channels(db: Session = Depends(get_db)):
    return db.query(models.Channel).all()


@router.post("/channels", response_model=schemas.ChannelOut)
def create_channel(payload: schemas.ChannelCreate, db: Session = Depends(get_db)):
    channel = models.Channel(**payload.model_dump())
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


@router.delete("/channels/{channel_id}")
def delete_channel(channel_id: int, db: Session = Depends(get_db)):
    channel = db.query(models.Channel).get(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Kanal tapılmadı")
    db.delete(channel)
    db.commit()
    return {"status": "deleted"}


# ---------- Yükləmə ----------
@router.post("/upload-to-youtube", response_model=schemas.UploadToYouTubeResponse)
def upload_to_youtube(payload: schemas.UploadToYouTubeRequest, db: Session = Depends(get_db)):
    # channel_id ya daxili DB ID-si (int), ya da frontend-in YouTube kanal ID-sidir (str).
    # Hər iki halda uyğun DB sətrini tapmağa çalışırıq; tapılmasa demo rejimində davam edirik
    # (kanal hələ backend-ə sinxronlaşdırılmayıbsa upload prosesini bloklamamaq üçün).
    channel = None
    if isinstance(payload.channel_id, int) or str(payload.channel_id).isdigit():
        channel = db.query(models.Channel).get(int(payload.channel_id))
    if not channel:
        channel = (
            db.query(models.Channel)
            .filter(models.Channel.youtube_channel_id == str(payload.channel_id))
            .first()
        )

    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    safe_id = str(payload.channel_id).replace("/", "_")
    local_path = os.path.join(settings.MEDIA_ROOT, f"upload_{safe_id}.mp4")
    try:
        resp = requests.get(payload.video_url, timeout=30)
        resp.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(resp.content)
    except requests.RequestException as exc:
        raise HTTPException(status_code=400, detail=f"Video yüklənə bilmədi: {exc}") from exc

    result = youtube_service.upload_video(
        refresh_token=channel.oauth_refresh_token if channel else None,
        video_path=local_path,
        title=payload.title,
        description=payload.description,
        tags=payload.tags,
    )
    return schemas.UploadToYouTubeResponse(
        youtube_id=result.get("youtube_id"), status=result.get("status", "failed")
    )


# ---------- OAuth (kanal sahibinin YouTube icazəsi) ----------
@router.get("/auth/youtube/login")
def youtube_login():
    """İstifadəçini Google OAuth razılıq ekranına yönləndirir."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="GOOGLE_CLIENT_ID .env-də təyin olunmayıb")
    scope = "https://www.googleapis.com/auth/youtube.upload+https://www.googleapis.com/auth/yt-analytics.readonly"
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        f"&response_type=code&access_type=offline&prompt=consent&scope={scope}"
    )
    return RedirectResponse(url)


@router.get("/auth/youtube/callback")
def youtube_callback(code: str, channel_id: int, db: Session = Depends(get_db)):
    """Google-dan gələn 'code'-u refresh_token-a çevirib DB-də kanala bağlayır."""
    channel = db.query(models.Channel).get(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Kanal tapılmadı")

    token_resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    token_resp.raise_for_status()
    tokens = token_resp.json()
    refresh_token = tokens.get("refresh_token")
    if refresh_token:
        # QEYD: prodakşnda bu sahə şifrələnmiş saxlanmalıdır (məs. Fernet ilə) —
        # README_DEPLOY.md-də nümunə var.
        channel.oauth_refresh_token = refresh_token
        channel.is_demo = False
        db.commit()
    return {"status": "connected", "channel_id": channel_id}
