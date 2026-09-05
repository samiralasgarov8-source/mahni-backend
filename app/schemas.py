"""
SECTION 7: Pydantic sxemaları — request/response body-lərin validasiyası.
Bunlar PROGRESS.md-də sadalanan API endpoint-lərinin dəqiq formasını əks etdirir.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------- SECTION 1: Mövzu + Mətn ----------
class FetchTextRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="İstifadəçinin verdiyi mövzu")
    source: str = "auto"


class FetchTextResponse(BaseModel):
    text_az: str


class TranslateTextRequest(BaseModel):
    text_az: str
    target_langs: list[str] = Field(default_factory=list, description="Boşdursa bütün 24+ dil")


class TranslateTextResponse(BaseModel):
    texts: dict[str, str]


# ---------- SECTION 2: Şəkil ----------
class FetchImagesRequest(BaseModel):
    query: str
    count: int = 6


class ImageResult(BaseModel):
    url: str
    source: str
    title: Optional[str] = None


class FetchImagesResponse(BaseModel):
    images: list[ImageResult]


# ---------- SECTION 3: TTS ----------
class GenerateTTSRequest(BaseModel):
    text: str
    lang: str = "az"
    voice: str = "female_1"
    speed: float = 1.0
    pitch: float = 1.0


class GenerateTTSResponse(BaseModel):
    audio_url: str
    duration_sec: float
    voice: str
    demo: bool = False


# ---------- SECTION 4: Video ----------
class GenerateVideoRequest(BaseModel):
    job_id: Optional[int] = None
    image_urls: list[str]
    audio_url: str
    slide_duration_sec: float = 4.0
    watermark_text: Optional[str] = None
    lang: str = "az"


class GenerateVideoResponse(BaseModel):
    video_url: str
    duration: str  # "MM:SS"


# ---------- SECTION 5: YouTube yükləmə ----------
class UploadToYouTubeRequest(BaseModel):
    video_url: str
    title: str
    description: str = ""
    # Frontend hələ kanalları backend DB-yə sinxronlaşdırmadığı üçün,
    # channel_id həm daxili DB ID-si (int), həm də frontend-in localStorage-dakı
    # YouTube kanal ID-si (str, məs. "UCxxxx") ola bilər — hər iki hal dəstəklənir.
    channel_id: int | str
    channel_token: Optional[str] = None  # frontend-dəki OAuth Client ID (hələlik informativ)
    tags: list[str] = Field(default_factory=list)


class UploadToYouTubeResponse(BaseModel):
    youtube_id: Optional[str] = None
    status: str  # uploaded | pending | failed


class ChannelCreate(BaseModel):
    name: str
    youtube_channel_id: Optional[str] = None
    language: str = "az"


class ChannelOut(BaseModel):
    id: int
    name: str
    youtube_channel_id: Optional[str] = None
    language: str
    is_demo: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- SECTION 6: Analitika ----------
class AnalyticsPoint(BaseModel):
    date: str
    subscribers: int
    views: int


class AnalyticsResponse(BaseModel):
    channel_id: int
    subs: int
    watchHours: float
    shortsViews90d: int
    totalViews: int
    history: list[AnalyticsPoint]


class RevenueResponse(BaseModel):
    channel_id: int
    estimatedCpm: float
    estimatedRpm: float
    monthlyEstimate: float
