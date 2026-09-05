"""
SECTION 7: SECTION 4-ün ("Video Yaratma") backend qarşılığı.
ffmpeg CLI istifadə olunur (server-də quraşdırılmış olmalıdır — README_DEPLOY.md-yə bax).
Strategiya: hər şəkli N saniyə göstər (Ken Burns effekti üçün sadə zoom),
audio-nu üstünə qoy, watermark mətnini drawtext ilə əlavə et.
"""
import os
import subprocess
import uuid

from ..config import get_settings

settings = get_settings()


def _download_to_tmp(url: str, tmp_dir: str, idx: int) -> str:
    import requests
    ext = ".jpg"
    local_path = os.path.join(tmp_dir, f"img_{idx}{ext}")
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    with open(local_path, "wb") as f:
        f.write(resp.content)
    return local_path


def render_video(*, image_urls: list[str], audio_path: str, slide_duration_sec: float = 4.0,
                  watermark_text: str | None = None, lang: str = "az") -> dict:
    """Şəkillərdən + audio-dan 9:16 formatında video render edir, ffmpeg ilə."""
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    job_id = uuid.uuid4().hex[:10]
    tmp_dir = os.path.join(settings.MEDIA_ROOT, f"tmp_{job_id}")
    os.makedirs(tmp_dir, exist_ok=True)

    local_images = [_download_to_tmp(url, tmp_dir, i) for i, url in enumerate(image_urls)]

    # ffmpeg concat üçün siyahı faylı yarat
    list_path = os.path.join(tmp_dir, "list.txt")
    with open(list_path, "w") as f:
        for img in local_images:
            f.write(f"file '{os.path.abspath(img)}'\n")
            f.write(f"duration {slide_duration_sec}\n")
        # Son şəkil ffmpeg concat-da təkrarlanmalıdır (bilinən qayda)
        if local_images:
            f.write(f"file '{os.path.abspath(local_images[-1])}'\n")

    output_filename = f"video_{job_id}.mp4"
    output_path = os.path.join(settings.MEDIA_ROOT, output_filename)

    vf_filters = ["scale=1080:1920:force_original_aspect_ratio=increase", "crop=1080:1920"]
    if watermark_text:
        safe_text = watermark_text.replace("'", "\\'").replace(":", "\\:")
        vf_filters.append(
            f"drawtext=text='{safe_text}':fontcolor=white@0.7:fontsize=28:"
            f"x=w-tw-20:y=h-th-20"
        )
    vf_chain = ",".join(vf_filters)

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", list_path,
        "-i", audio_path,
        "-vf", vf_chain,
        "-c:v", "libx264", "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg xətası: {result.stderr[-2000:]}")

    duration = _probe_duration(output_path)
    minutes, seconds = divmod(int(duration), 60)

    return {
        "video_url": f"{settings.PUBLIC_BASE_URL}/media/{output_filename}",
        "duration": f"{minutes:02d}:{seconds:02d}",
    }


def _probe_duration(path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0
