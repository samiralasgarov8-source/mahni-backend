"""SECTION 7: SECTION 6-nın API endpoint-ləri (analitika + gəlir).
Bu, frontend-dəki demo/localStorage simulyasiyasını server tərəfinə köçürür,
həm də real YouTube Analytics/AdSense API-lərinə keçid yeri təmin edir.
"""
import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas, models
from ..database import get_db
from ..services import youtube_service, adsense_service

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/analytics/{channel_id}", response_model=schemas.AnalyticsResponse)
def get_analytics(channel_id: int, db: Session = Depends(get_db)):
    channel = db.query(models.Channel).get(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Kanal tapılmadı")

    data = youtube_service.get_channel_analytics(
        channel_db_key=f"{channel.id}-{channel.name}",
        refresh_token=channel.oauth_refresh_token,
        youtube_channel_id=channel.youtube_channel_id,
    )

    # Bugünkü nəticəni DB-yə snapshot kimi yaz (tarixçə saxlamaq üçün)
    snapshot = models.AnalyticsSnapshot(
        channel_id=channel.id,
        date=dt.datetime.utcnow(),
        subscribers=data["subs"],
        watch_hours_365d=data.get("watchHours") or 0,
        shorts_views_90d=data.get("shortsViews90d") or 0,
        total_views=data["totalViews"],
    )
    db.add(snapshot)
    db.commit()

    return schemas.AnalyticsResponse(
        channel_id=channel.id,
        subs=data["subs"],
        watchHours=data.get("watchHours") or 0,
        shortsViews90d=data.get("shortsViews90d") or 0,
        totalViews=data["totalViews"],
        history=[schemas.AnalyticsPoint(**h) for h in data.get("history", [])],
    )


@router.get("/revenue/{channel_id}", response_model=schemas.RevenueResponse)
def get_revenue(channel_id: int, db: Session = Depends(get_db)):
    channel = db.query(models.Channel).get(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Kanal tapılmadı")

    latest = (
        db.query(models.AnalyticsSnapshot)
        .filter(models.AnalyticsSnapshot.channel_id == channel_id)
        .order_by(models.AnalyticsSnapshot.date.desc())
        .first()
    )
    monthly_views = (latest.total_views if latest else 0) or 0
    result = adsense_service.estimate_revenue(monthly_views=monthly_views)
    return schemas.RevenueResponse(channel_id=channel_id, **result)
