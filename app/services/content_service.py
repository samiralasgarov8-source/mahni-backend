"""
SECTION 7: SECTION 1-in ("Mövzu + Mətn Mənbəyi") backend qarşılığı.
Mətn axtarışı üçün heç bir açar tələb etməyən sadə strategiya istifadə olunur
(Wikipedia REST API, pulsuzdur). Tərcümə üçün `deep-translator` (Google Translate
frontend-inə əsaslanan pulsuz kitabxana) istifadə olunur.
"""
import requests

from ..config import get_settings

settings = get_settings()

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False


def _wikipedia_search_title(topic: str) -> str | None:
    """Mövzu sərbəst ifadə (məs. 'nar haqqında məlumat') olsa belə, Wikipedia-nın
    axtarış API-si (opensearch) ən uyğun məqalə başlığını tapır. Dəqiq başlıq
    tələb edən köhnə üsuldan fərqli olaraq, bu, təxmini uyğunluqla da işləyir."""
    try:
        resp = requests.get(
            "https://az.wikipedia.org/w/api.php",
            params={
                "action": "opensearch",
                "search": topic,
                "limit": 1,
                "namespace": 0,
                "format": "json",
            },
            timeout=6,
        )
        if resp.status_code == 200:
            data = resp.json()
            titles = data[1] if len(data) > 1 else []
            if titles:
                return titles[0]
    except (requests.RequestException, ValueError, IndexError):
        pass
    return None


def _wikipedia_summary(title: str) -> str | None:
    try:
        resp = requests.get(
            "https://az.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.quote(title),
            timeout=6,
        )
        if resp.status_code == 200:
            extract = resp.json().get("extract")
            if extract:
                return extract
    except requests.RequestException:
        pass
    return None


def _gemini_summary(topic: str) -> str | None:
    """Wikipedia-da uyğun məqalə tapılmayanda, pulsuz Gemini API ilə mövzu
    haqqında qısa, Azərbaycan dilində məlumat mətni yaradır. GEMINI_API_KEY
    boşdursa, bu funksiya sadəcə None qaytarır (çağıran tərəf öz fallback-ini işlədir)."""
    if not settings.GEMINI_API_KEY:
        return None
    try:
        resp = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
            f"?key={settings.GEMINI_API_KEY}",
            json={
                "contents": [{
                    "parts": [{
                        "text": (
                            f"'{topic}' mövzusu haqqında Azərbaycan dilində, 3-5 cümlədən ibarət, "
                            "sadə və dəqiq bir məlumat mətni yaz. Yalnız mətnin özünü qaytar, "
                            "başqa izahat, başlıq və ya markdown əlavə etmə."
                        )
                    }]
                }]
            },
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates") or []
            if candidates:
                parts = candidates[0].get("content", {}).get("parts") or []
                text = "".join(p.get("text", "") for p in parts).strip()
                if text:
                    return text
    except (requests.RequestException, ValueError, KeyError, IndexError):
        pass
    return None


def fetch_text_for_topic(topic: str, source: str = "auto") -> str:
    """Mövzu üçün qısa, mənbəli mətn gətirir:
    1) Wikipedia axtarışı (sərbəst ifadələrlə də işləyir, dəqiq başlıq tələb etmir)
    2) Tapılmasa və GEMINI_API_KEY qurulubsa, AI (Gemini) ilə mətn yaradılır
    3) Heç biri alınmasa, istifadəçiyə əl ilə redaktə üçün fallback mesaj qaytarılır."""
    wiki_title = _wikipedia_search_title(topic)
    if wiki_title:
        extract = _wikipedia_summary(wiki_title)
        if extract:
            return extract

    ai_text = _gemini_summary(topic)
    if ai_text:
        return ai_text

    return f"{topic} haqqında qısa məlumat: bu mövzu barədə ətraflı mətn hələ tapılmadı, xahiş olunur əl ilə redaktə edin."


def translate_text(text_az: str, target_langs: list[str]) -> dict[str, str]:
    """Azərbaycan dilindəki mətni istənilən dillərə tərcümə edir."""
    result = {"az": text_az}
    if not target_langs:
        return result
    if not TRANSLATOR_AVAILABLE:
        # Kitabxana yoxdursa, təhlükəsiz fallback: eyni mətni qaytar (frontend xəbərdar edir)
        for lang in target_langs:
            result[lang] = text_az
        return result

    for lang in target_langs:
        if lang == "az":
            continue
        try:
            result[lang] = GoogleTranslator(source="az", target=lang).translate(text_az)
        except Exception as exc:  # noqa: BLE001 — tərcümə xətası bütün sorğunu batırmamalıdır
            result[lang] = text_az
            result[f"{lang}_error"] = str(exc)
    return result
