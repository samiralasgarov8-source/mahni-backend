"""
SECTION 7: SECTION 2-nin ("Şəkil + Animasyon") backend qarşılığı.
Pexels API pulsuzdur (açar tələb edir, https://www.pexels.com/api/ -dən alınır).
Açar yoxdursa placeholder şəkillər qaytarılır ki, video render bloklanmasın.
"""
import requests

from ..config import get_settings

settings = get_settings()

PLACEHOLDER_IMAGES = [
    "https://picsum.photos/seed/{seed}/1080/1920",
]


def fetch_images(query: str, count: int = 6) -> list[dict]:
    if settings.PEXELS_API_KEY:
        try:
            resp = requests.get(
                "https://api.pexels.com/v1/search",
                params={"query": query, "per_page": count, "orientation": "portrait"},
                headers={"Authorization": settings.PEXELS_API_KEY},
                timeout=8,
            )
            if resp.status_code == 200:
                photos = resp.json().get("photos", [])
                return [
                    {"url": p["src"]["portrait"], "source": "pexels", "title": p.get("alt") or query}
                    for p in photos
                ]
        except requests.RequestException:
            pass

    # ---- Fallback: placeholder şəkillər (PEXELS_API_KEY yoxdursa) ----
    return [
        {"url": PLACEHOLDER_IMAGES[0].format(seed=f"{query}-{i}"), "source": "placeholder", "title": query}
        for i in range(count)
    ]
