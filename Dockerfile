# SECTION 7: Docker image — ffmpeg tələb olunduğu üçün (video render, SECTION 4)
# Render.com-un adi Python runtime-ı ffmpeg-i əvvəlcədən quraşdırmır,
# ona görə Docker runtime istifadə edirik (render.yaml-da runtime: docker).
FROM python:3.12-slim

# ffmpeg: video render üçün (SECTION 4). git: bəzi pip paketləri üçün lazım ola bilər.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/media

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
