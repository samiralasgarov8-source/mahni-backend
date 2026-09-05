"""
SECTION 7: Verilənlər bazası modelləri.
Bunlar frontend-dəki (SECTION 5 kanal siyahısı + SECTION 6 analitika tarixçəsi)
localStorage strukturunu server tərəfində əvəzləyir ki, data brauzer
təmizlənəndə itməsin və çoxlu istifadəçi/cihaz arasında sinxron olsun.
"""
import datetime as dt

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import relationship

from .database import Base


class Channel(Base):
    """SECTION 5-dəki 'kanal' sətrinin server qarşılığı."""
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    youtube_channel_id = Column(String(64), unique=True, index=True, nullable=True)
    language = Column(String(10), default="az")
    oauth_refresh_token = Column(Text, nullable=True)   # şifrələnmiş saxlanmalıdır (bax README)
    is_demo = Column(Boolean, default=True)             # real OAuth bağlanana qədər demo rejimi
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    jobs = relationship("VideoJob", back_populates="channel")
    analytics = relationship("AnalyticsSnapshot", back_populates="channel")


class VideoJob(Base):
    """SECTION 1-4-ün (mətn->şəkil->səs->video) tam boru xəttinin bir icrası."""
    __tablename__ = "video_jobs"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=True)
    topic = Column(String(500), nullable=False)
    status = Column(String(30), default="pending")
    # pending -> fetching_text -> translating -> fetching_images ->
    # generating_tts -> rendering_video -> uploading -> done | failed
    progress_pct = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    text_az = Column(Text, nullable=True)
    translations_json = Column(Text, nullable=True)   # JSON string: {"en": "...", "ru": "...", ...}
    video_url = Column(String(500), nullable=True)
    youtube_video_id = Column(String(64), nullable=True)

    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    channel = relationship("Channel", back_populates="jobs")


class AnalyticsSnapshot(Base):
    """SECTION 6-nın localStorage tarixçəsinin server qarşılığı — hər gün 1 sətir."""
    __tablename__ = "analytics_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    date = Column(DateTime, default=dt.datetime.utcnow)

    subscribers = Column(Integer, default=0)
    watch_hours_365d = Column(Float, default=0)
    shorts_views_90d = Column(Integer, default=0)
    total_views = Column(Integer, default=0)

    estimated_cpm = Column(Float, nullable=True)
    estimated_rpm = Column(Float, nullable=True)
    estimated_monthly_revenue = Column(Float, nullable=True)

    channel = relationship("Channel", back_populates="analytics")
