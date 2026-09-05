"""
SECTION 7: SECTION 1-in ("Mövzu + Mətn Mənbəyi") backend qarşılığı.
Mətn axtarışı üçün heç bir açar tələb etməyən sadə strategiya istifadə olunur
(Wikipedia REST/Action API, pulsuzdur). Tərcümə üçün `deep-translator` (Google
Translate frontend-inə əsaslanan pulsuz kitabxana) istifadə olunur.
"""
import requests

from ..config import get_settings

settings = get_settings()

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False

# Tam məqalə mətni bu qədər simvoldan uzun olmasın (çox uzun mətn TTS/video
# üçün əlverişsizdir, amma əvvəlki "summary" (tək paraqraf) versiyasından
# xeyli genişdir).
MAX_EXTRACT_CHARS = 2500

# Azərbaycan Wikipediyasındakı məqalə bundan qısadırsa (çox vaxt stub/1-cümlə
# olur), daha zəngin dillərdən (tr/en) məqaləni gətirib Azərbaycan dilinə
# tərcümə edirik ki, istifadəçiyə həqiqətən "bir cümlə" deyil, dolğun mətn getsin.
MIN_ACCEPTABLE_CHARS = 350


def _wiki_search_title(topic: str, lang: str) -> str | None:
    try:
        resp = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={"action": "opensearch", "search": topic, "limit": 1, "namespace": 0, "format": "json"},
            headers={"User-Agent": "MahniStudiyasi/1.0 (auto-video-generator; contact: n/a)"},
            timeout=6,
        )
        print(f"[content_service] opensearch[{lang}] status={resp.status_code} topic={topic!r}")
        if resp.status_code == 200:
            data = resp.json()
            titles = data[1] if len(data) > 1 else []
            print(f"[content_service] opensearch[{lang}] titles={titles}")
            if titles:
                return titles[0]
        else:
            print(f"[content_service] opensearch[{lang}] non-200 body={resp.text[:300]!r}")
    except (requests.RequestException, ValueError, IndexError) as exc:
        print(f"[content_service] opensearch[{lang}] EXCEPTION: {exc!r}")
    return None


def _wiki_full_extract(title: str, lang: str) -> str | None:
    try:
        resp = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={"action": "query", "prop": "extracts", "explaintext": 1, "redirects": 1, "titles": title, "format": "json"},
            headers={"User-Agent": "MahniStudiyasi/1.0 (auto-video-generator; contact: n/a)"},
            timeout=8,
        )
        print(f"[content_service] full_extract[{lang}] status={resp.status_code} title={title!r}")
        if resp.status_code == 200:
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                extract = (page.get("extract") or "").strip()
                if extract:
                    if len(extract) > MAX_EXTRACT_CHARS:
                        cut = extract.rfind(". ", 0, MAX_EXTRACT_CHARS)
                        extract = extract[: cut + 1] if cut > 0 else extract[:MAX_EXTRACT_CHARS]
                    return extract
        else:
            print(f"[content_service] full_extract[{lang}] non-200 body={resp.text[:300]!r}")
    except requests.RequestException as exc:
        print(f"[content_service] full_extract[{lang}] EXCEPTION: {exc!r}")
    return None


def _wiki_summary(title: str, lang: str) -> str | None:
    try:
        resp = requests.get(
            f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.quote(title),
            headers={"User-Agent": "MahniStudiyasi/1.0 (auto-video-generator; contact: n/a)"},
            timeout=6,
        )
        print(f"[content_service] summary[{lang}] status={resp.status_code} title={title!r}")
        if resp.status_code == 200:
            extract = resp.json().get("extract")
            if extract:
                return extract
        else:
            print(f"[content_service] summary[{lang}] non-200 body={resp.text[:300]!r}")
    except requests.RequestException as exc:
        print(f"[content_service] summary[{lang}] EXCEPTION: {exc!r}")
    return None


def _translate_to_az(text: str) -> str:
    if not TRANSLATOR_AVAILABLE or not text:
        return text
    try:
        return GoogleTranslator(source="auto", target="az").translate(text)
    except Exception as exc:  # noqa: BLE001
        print(f"[content_service] translate_to_az EXCEPTION: {exc!r}")
        return text


def _best_wikipedia_text(topic: str) -> str | None:
    """Əvvəlcə Azərbaycan Wikipediyasında axtarır. Tapılan mətn çox qısadırsa
    (çox vaxt stub/disambiguation səhifəsi olur), Türk və İngilis
    Wikipediyalarından daha dolğun məqaləni gətirib Azərbaycan dilinə tərcümə
    edir və daha uzun olanı seçir."""
    best_text = None
    best_len = 0

    az_title = _wiki_search_title(topic, "az")
    if az_title:
        az_text = _wiki_full_extract(az_title, "az") or _wiki_summary(az_title, "az")
        if az_text:
            best_text, best_len = az_text, len(az_text)

    if best_len >= MIN_ACCEPTABLE_CHARS:
        return best_text

    for lang in ("tr", "en"):
        title = _wiki_search_title(topic, lang)
        if not title:
            continue
        extract = _wiki_full_extract(title, lang) or _wiki_summary(title, lang)
        if not extract:
            continue
        if len(extract) > best_len:
            translated = _translate_to_az(extract)
            if len(translated) > best_len:
                best_text, best_len = translated, len(translated)
        if best_len >= MIN_ACCEPTABLE_CHARS:
            break

    return best_text


def _gemini_summary(topic: str) -> str | None:
    # getattr ilə: GEMINI_API_KEY .env/config.py-da hələ təyin olunmayıbsa belə
    # (köhnə Settings sinifi), bu, AttributeError ilə bütün sorğunu batırmasın.
    gemini_key = getattr(settings, "GEMINI_API_KEY", "")
    if not gemini_key:
        print("[content_service] GEMINI_API_KEY boşdur, AI fallback atlanır")
        return None
    try:
        resp = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
            f"?key={gemini_key}",
            json={"contents": [{"parts": [{"text": (
                f"'{topic}' mövzusu haqqında Azərbaycan dilində, 6-10 cümlədən ibarət, "
                "ətraflı və dəqiq bir məlumat mətni yaz. Yalnız mətnin özünü qaytar, "
                "başqa izahat, başlıq və ya markdown əlavə etmə."
            )}]}]},
            timeout=20,
        )
        print(f"[content_service] gemini status={resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates") or []
            if candidates:
                parts = candidates[0].get("content", {}).get("parts") or []
                text = "".join(p.get("text", "") for p in parts).strip()
                if text:
                    return text
        else:
            print(f"[content_service] gemini non-200 body={resp.text[:300]!r}")
    except (requests.RequestException, ValueError, KeyError, IndexError) as exc:
        print(f"[content_service] gemini EXCEPTION: {exc!r}")
    return None


def fetch_text_for_topic(topic: str, source: str = "auto") -> str:
    """1) AZ Wikipedia tam mətn -> 2) qısadırsa TR/EN Wikipedia + tərcümə ->
    3) hələ də qısadırsa Gemini (açar varsa) -> 4) heç nə tapılmasa fallback mesaj."""
    wiki_text = _best_wikipedia_text(topic)

    if wiki_text and len(wiki_text) >= MIN_ACCEPTABLE_CHARS:
        return wiki_text

    ai_text = _gemini_summary(topic)
    if ai_text and (not wiki_text or len(ai_text) > len(wiki_text)):
        return ai_text

    if wiki_text:
        return wiki_text

    return f"{topic} haqqında qısa məlumat: bu mövzu barədə ətraflı mətn hələ tapılmadı, xahiş olunur əl ilə redaktə edin."


def translate_text(text_az: str, target_langs: list[str]) -> dict[str, str]:
    result = {"az": text_az}
    if not target_langs:
        return result
    if not TRANSLATOR_AVAILABLE:
        for lang in target_langs:
            result[lang] = text_az
        return result

    for lang in target_langs:
        if lang == "az":
            continue
        try:
            result[lang] = GoogleTranslator(source="az", target=lang).translate(text_az)
        except Exception as exc:  # noqa: BLE001
            result[lang] = text_az
            result[f"{lang}_error"] = str(exc)
    return result
