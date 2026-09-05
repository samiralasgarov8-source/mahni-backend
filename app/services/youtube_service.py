"""
SECTION 7: YouTube Data API v3 + YouTube Analytics API inteqrasiyası.

REAL rejimə keçmək üçün lazım olanlar (README_DEPLOY.md-də addım-addım izah var):
  1. Google Cloud Console-da layihə yarat, "YouTube Data API v3" və
     "YouTube Analytics API"-ni aktivləşdir.
  2. OAuth 2.0 Client ID (Web application) yarat, .env-ə GOOGLE_CLIENT_ID/SECRET yaz.
  3. Hər kanal admini /api/auth/youtube/login ilə OAuth icazəsi verir,
     refresh_token DB-də (Channel.oauth_refresh_token) saxlanılır.

Bu fayl `google-api-python-client` və `google-auth-oauthlib` kitabxanalarından
istifadə edir. Şəbəkə/API açarları olmadıqda funksiyalar demo (simulyasiya)
nəticəsi qaytarır ki, frontend inkişafı bloklanmasın.
"""
from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta

from ..config import get_settings

settings = get_settings()

try:
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False


def _is_real_mode() -> bool:
    """Real Google API çağırışı üçün açarlar mövcuddurmu?"""
    return (
        GOOGLE_LIBS_AVAILABLE
        and bool(settings.GOOGLE_CLIENT_ID)
        and bool(settings.GOOGLE_CLIENT_SECRET)
    )


def _seeded_rng(channel_key: str) -> random.Random:
    """SECTION 6-dakı frontend məntiqi ilə eyni: kanal adına görə sabit,
    amma kanallar arası fərqli demo rəqəmlər."""
    seed = int(hashlib.md5(channel_key.encode()).hexdigest(), 16) % (10**8)
    return random.Random(seed)


def build_youtube_client(refresh_token: str):
    """OAuth refresh_token-dan işlək bir YouTube API client qurur (real rejim)."""
    if not _is_real_mode():
        raise RuntimeError(
            "Google API kitabxanaları/açarları quraşdırılmayıb — demo rejimindən çıxmaq üçün "
            ".env-ə GOOGLE_CLIENT_ID/SECRET yazın və `pip install google-api-python-client "
            "google-auth-oauthlib` edin."
        )
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
    )
    return build("youtube", "v3", credentials=creds)


def upload_video(*, refresh_token: str | None, video_path: str, title: str,
                  description: str, tags: list[str]) -> dict:
    """Videonu YouTube-a yükləyir. refresh_token yoxdursa (demo kanal) simulyasiya edir."""
    if refresh_token and _is_real_mode():
        youtube = build_youtube_client(refresh_token)
        body = {
            "snippet": {"title": title, "description": description, "tags": tags},
            "status": {"privacyStatus": "private"},  # təhlükəsizlik üçün default private
        }
        # Böyük fayllar üçün resumable upload lazımdır — bax googleapiclient.http.MediaFileUpload
        from googleapiclient.http import MediaFileUpload
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        return {"youtube_id": response.get("id"), "status": "uploaded"}

    # ---- Demo rejim ----
    fake_id = hashlib.md5(f"{title}{datetime.utcnow()}".encode()).hexdigest()[:11]
    return {"youtube_id": fake_id, "status": "pending", "note": "DEMO REJİM — real yükləmə üçün OAuth qoşun"}


def get_channel_analytics(*, channel_db_key: str, refresh_token: str | None,
                           youtube_channel_id: str | None) -> dict:
    """Real Analytics API və ya (açar yoxdursa) SECTION 6 ilə eyni deterministik demo data."""
    if refresh_token and youtube_channel_id and _is_real_mode():
        youtube = build_youtube_client(refresh_token)
        stats = youtube.channels().list(part="statistics", id=youtube_channel_id).execute()
        items = stats.get("items", [])
        if items:
            s = items[0]["statistics"]
            subs = int(s.get("subscriberCount", 0))
            total_views = int(s.get("viewCount", 0))
            # Watch-hours və shorts-views YouTube Analytics API (fərqli endpoint) tələb edir —
            # README_DEPLOY.md-də tam sorğu nümunəsi var.
            return {
                "subs": subs,
                "totalViews": total_views,
                "watchHours": None,      # Analytics API ilə doldurulacaq
                "shortsViews90d": None,  # Analytics API ilə doldurulacaq
                "history": [],
                "mode": "real",
            }

    # ---- Demo rejim: SECTION 6 frontend məntiqi ilə eyni seed alqoritmi ----
    rng = _seeded_rng(channel_db_key)
    base_subs = rng.randint(50, 5000)
    base_views = rng.randint(1000, 200000)
    history = []
    subs, views_total = base_subs, base_views
    for i in range(30, 0, -1):
        day = datetime.utcnow() - timedelta(days=i)
        daily_views = rng.randint(50, 3000)
        subs += rng.randint(0, 15)
        views_total += daily_views
        history.append({"date": day.strftime("%Y-%m-%d"), "subscribers": subs, "views": daily_views})

    return {
        "subs": subs,
        "totalViews": views_total,
        "watchHours": round(views_total * 0.05, 1),   # təxmini: baxışın ~3 dəq/60 = saat
        "shortsViews90d": int(views_total * 0.6),
        "history": history,
        "mode": "demo",
    }
