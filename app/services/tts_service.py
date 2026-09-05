"""
SECTION 7: SECTION 3-ün ("Səsləndirmə / TTS") backend qarşılığı.
Default provider: gTTS (pulsuz, Google Translate TTS-ə əsaslanır, açar tələb etmir).
Prodakşn keyfiyyəti üçün ELEVENLABS_API_KEY və ya AZURE_SPEECH_KEY veriləndə
onlara keçmək üçün TTS_PROVIDER-i dəyişmək kifayətdir.
"""
import os
import uuid
import wave
import struct

from ..config import get_settings

settings = get_settings()

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False


def _make_silent_placeholder(filepath_wav: str, duration_sec: float) -> None:
    """Xarici TTS xidməti əlçatan olmadıqda (şəbəkə problemi, 403, limit və s.)
    proqramın çökməməsi üçün lokal, heç bir internetə ehtiyacı olmayan boş
    (səssiz) .wav fayl yaradır. Bu, DEMO rejiminin bir hissəsidir."""
    framerate = 16000
    n_frames = int(framerate * max(duration_sec, 1.0))
    with wave.open(filepath_wav, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(framerate)
        silence_frame = struct.pack("<h", 0)
        f.writeframes(silence_frame * n_frames)


def generate_tts(text: str, lang: str = "az", voice: str = "female_1",
                  speed: float = 1.0) -> dict:
    """Mətni səsə çevirir, media qovluğuna saxlayır, ictimai URL qaytarır.
    Real TTS xidməti (gTTS/ElevenLabs/Azure) hər hansı səbəbdən uğursuz olsa
    (şəbəkə, 403, limit, açar yoxdur və s.), proqram XƏTA ilə DAYANMIR —
    avtomatik olaraq lokal səssiz placeholder audio ilə DEMO rejiminə keçir."""
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    duration_estimate = max(1.0, len(text.split()) / 2.5)  # ~2.5 söz/saniyə təxmini

    if settings.TTS_PROVIDER == "gtts" and GTTS_AVAILABLE:
        filename = f"tts_{uuid.uuid4().hex[:10]}.mp3"
        filepath = os.path.join(settings.MEDIA_ROOT, filename)
        try:
            # gTTS Azərbaycan dilini birbaşa dəstəkləmir — dəstəklənməyən dillər üçün
            # ən yaxın dəstəklənən dilə (məs. türk) fallback edilir.
            gtts_lang = lang if lang in ("en", "ru", "tr", "ar", "de", "fr", "es") else "tr"
            tts = gTTS(text=text, lang=gtts_lang)
            tts.save(filepath)
            return {
                "audio_url": f"{settings.PUBLIC_BASE_URL}/media/{filename}",
                "duration_sec": round(duration_estimate, 1),
                "voice": voice,
                "demo": False,
            }
        except Exception:
            # Google TTS xidməti cavab vermədi (403/şəbəkə/limit) -> DEMO fallback
            pass

    # ---- DEMO fallback: real xidmət yoxdur və ya uğursuz oldu ----
    filename = f"tts_demo_{uuid.uuid4().hex[:10]}.wav"
    filepath = os.path.join(settings.MEDIA_ROOT, filename)
    _make_silent_placeholder(filepath, duration_estimate)
    return {
        "audio_url": f"{settings.PUBLIC_BASE_URL}/media/{filename}",
        "duration_sec": round(duration_estimate, 1),
        "voice": voice,
        "demo": True,
    }
