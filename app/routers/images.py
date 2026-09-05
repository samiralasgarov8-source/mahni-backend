"""SECTION 7: SECTION 2-nin API endpoint-i (şəkil mənbəyi)."""
from fastapi import APIRouter

from .. import schemas
from ..services import image_service

router = APIRouter(prefix="/api", tags=["images"])


@router.post("/fetch-images", response_model=schemas.FetchImagesResponse)
def fetch_images(payload: schemas.FetchImagesRequest):
    images = image_service.fetch_images(payload.query, payload.count)
    return schemas.FetchImagesResponse(images=[schemas.ImageResult(**i) for i in images])
