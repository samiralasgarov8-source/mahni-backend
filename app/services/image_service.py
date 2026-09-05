"""
SECTION 7: SECTION 2-nin ("Şəkil + Animasyon") backend qarşılığı.
Öncəlik sırası:
1) Pexels API (əla keyfiyyət, açar tələb edir: https://www.pexels.com/api/)
2) Wikimedia Commons axtarışı (PULSUZ, açar tələb etmir, mövzuya uyğun REAL
   şəkillər qaytarır — əvvəlki "picsum.photos" fallback-ı isə tamamilə TƏSADÜFİ,
   mövzu ilə əlaqəsi olmayan stok şəkillər verirdi)
3) Yalnız hər ikisi uğursuz olsa (şəbəkə problemi və s.), son çarə kimi
   picsum.photos placeholder-ları (bu, artıq nadir hala düşür)
"""
import requests

from ..config import get_settings

settings = get_settings()

PLACEHOLDER_IMAGES = [
    "https://picsum.photos/seed/{seed}/1080/1920",
]


def _fetch_from_pexels(query: str, count: int) -> list[dict]:
    if not settings.PEXELS_API_KEY:
        return []
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "per_page": count, "orientation": "portrait"},
            headers={"Authorization": settings.PEXELS_API_KEY},
            timeout=8,
        )
        print(f"[image_service] pexels status={resp.status_code} query={query!r}")
        if resp.status_code == 200:
            photos = resp.json().get("photos", [])
            return [
                {"url": p["src"]["portrait"], "source": "pexels", "title": p.get("alt") or query}
                for p in photos
            ]
        print(f"[image_service] pexels non-200 body={resp.text[:300]!r}")
    except requests.RequestException as exc:
        print(f"[image_service] pexels EXCEPTION: {exc!r}")
    return []


def _fetch_from_commons(query: str, count: int) -> list[dict]:
    """Wikimedia Commons-un öz axtarış API-si — açar tələb etmir, mövzuya
    uyğun real şəkillər (foto, illüstrasiya) qaytarır. generator=search ilə
    sorğuya uyğun fayl səhifələrini tapıb, imageinfo ilə birbaşa URL-lərini alırıq."""
    try:
        resp = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": f"filetype:bitmap {query}",
                "gsrnamespace": 6,  # File: namespace
                "gsrlimit": count,
                "prop": "imageinfo",
                "iiprop": "url|extmetadata",
                "iiurlwidth": 1080,
                "format": "json",
            },
            headers={"User-Agent": "MahniStudiyasi/1.0 (auto-video-generator; contact: n/a)"},
            timeout=8,
        )
        print(f"[image_service] commons status={resp.status_code} query={query!r}")
        if resp.status_code != 200:
            print(f"[image_service] commons non-200 body={resp.text[:300]!r}")
            return []
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        results = []
        for page in pages.values():
            infos = page.get("imageinfo") or []
            if not infos:
                continue
            info = infos[0]
            url = info.get("thumburl") or info.get("url")
            if not url:
                continue
            # Yalnız real şəkil formatları (icon/svg/pdf s. video üçün əlverişsizdir)
            if not url.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            results.append({"url": url, "source": "wikimedia_commons", "title": page.get("title", query)})
        print(f"[image_service] commons found={len(results)}")
        return results[:count]
    except (requests.RequestException, ValueError) as exc:
        print(f"[image_service] commons EXCEPTION: {exc!r}")
        return []


def fetch_images(query: str, count: int = 6) -> list[dict]:
    images = _fetch_from_pexels(query, count)
    if images:
        return images

    images = _fetch_from_commons(query, count)
    if images:
        return images

    # ---- Son çarə: heç bir mənbə işləmədi (şəbəkə problemi və s.) ----
    print(f"[image_service] hər iki mənbə boş qaytardı, placeholder işlədilir: {query!r}")
    return [
        {"url": PLACEHOLDER_IMAGES[0].format(seed=f"{query}-{i}"), "source": "placeholder", "title": query}
        for i in range(count)
    ]
