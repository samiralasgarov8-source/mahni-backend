"""
SECTION 7: AdSense gəlir hesablaması.

Real AdSense Management API OAuth + `ADSENSE_ACCOUNT_ID` tələb edir və
yalnız YouTube-un özü tərəfindən monetizasiya təsdiqlənmiş kanallar üçün
məlumat qaytarır. Açar yoxdursa (əksər hallarda inkişaf zamanı), SECTION 6-dakı
frontend kalkulyator düsturu ilə eyni təxmini istifadə olunur ki, nəticə tutarlı qalsın.
"""
from ..config import get_settings

settings = get_settings()

# SECTION 6-dakı frontend defolt dəyərləri ilə sinxron saxlanılıb
DEFAULT_CPM = 2.5     # 1000 baxışa təxmini reklam gəliri (USD)
YOUTUBE_SHARE = 0.55  # YouTube-un yaradıcıya verdiyi pay (~55%)


def estimate_revenue(*, monthly_views: int, cpm: float | None = None) -> dict:
    cpm = cpm if cpm is not None else DEFAULT_CPM
    rpm = cpm * YOUTUBE_SHARE
    monthly_estimate = (monthly_views / 1000.0) * rpm
    return {
        "estimatedCpm": round(cpm, 2),
        "estimatedRpm": round(rpm, 2),
        "monthlyEstimate": round(monthly_estimate, 2),
    }
