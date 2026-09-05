"""SECTION 7: SECTION 4-ün API endpoint-i (video render, ffmpeg)."""
import os

from fastapi import APIRouter, HTTPException
import requests

from .. import schemas
from ..config import get_settings
from ..services import video_service

router = APIRouter(prefix="/api", tags=["video"])
settings = get_settings()


@router.post("/generate-video", response_model=schemas.GenerateVideoResponse)
def generate_video(payload: schemas.GenerateVideoRequest):
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    local_audio = os.path.join(settings.MEDIA_ROOT, f"audio_{payload.job_id or 'tmp'}.mp3")
    try:
        resp = requests.get(payload.audio_url, timeout=15)
        resp.raise_for_status()
        with open(local_audio, "wb") as f:
            f.write(resp.content)
    except requests.RequestException as exc:
        raise HTTPException(status_code=400, detail=f"Audio yüklənə bilmədi: {exc}") from exc

    try:
        result = video_service.render_video(
            image_urls=payload.image_urls,
            audio_path=local_audio,
            slide_duration_sec=payload.slide_duration_sec,
            watermark_text=payload.watermark_text,
            lang=payload.lang,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return schemas.GenerateVideoResponse(**result)
