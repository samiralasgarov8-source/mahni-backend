"""SECTION 7: SECTION 3-ün API endpoint-i (səsləndirmə)."""
from fastapi import APIRouter, HTTPException

from .. import schemas
from ..services import tts_service

router = APIRouter(prefix="/api", tags=["tts"])


@router.post("/generate-tts", response_model=schemas.GenerateTTSResponse)
def generate_tts(payload: schemas.GenerateTTSRequest):
    try:
        result = tts_service.generate_tts(
            text=payload.text, lang=payload.lang, voice=payload.voice, speed=payload.speed
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return schemas.GenerateTTSResponse(**result)
