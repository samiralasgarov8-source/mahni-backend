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


def fetch_text_for_topic(topic: str, source: str = "auto") -> str:
    """Mövzu üçün qısa, mənbəli mətn gətirir. Wikipedia-da tapılmasa, mövzunu
    özü sadə bir giriş cümləsi ilə qaytarır (frontend istifadəçiyə əl ilə
    redaktə imkanı verir)."""
    try:
        resp = requests.get(
            "https://az.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.quote(topic),
            timeout=6,
        )
        if resp.status_code == 200:
            data = resp.json()
            extract = data.get("extract")
            if extract:
                return extract
    except requests.RequestException:
        pass
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
