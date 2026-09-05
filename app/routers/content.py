"""SECTION 7: SECTION 1-in API endpoint-ləri (mövzu -> mətn -> tərcümə)."""
from fastapi import APIRouter

from .. import schemas
from ..services import content_service

router = APIRouter(prefix="/api", tags=["content"])


@router.post("/fetch-text", response_model=schemas.FetchTextResponse)
def fetch_text(payload: schemas.FetchTextRequest):
    text = content_service.fetch_text_for_topic(payload.topic, payload.source)
    return schemas.FetchTextResponse(text_az=text)


@router.post("/translate-text", response_model=schemas.TranslateTextResponse)
def translate_text(payload: schemas.TranslateTextRequest):
    texts = content_service.translate_text(payload.text_az, payload.target_langs)
    return schemas.TranslateTextResponse(texts=texts)
