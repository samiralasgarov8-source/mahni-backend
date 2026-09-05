# SECTION 7: Backend Kuruluşu — Quraşdırma və Deploy Bələdçisi

Bu backend, HTML frontend-in (SECTION 1-6) demo/localStorage rejimlərini əvəz
edərək real data ilə işləməsini təmin edir. **Heç bir açar verməsən belə**
tətbiq demo rejimində tam işləyir — açarları tədricən əlavə edə bilərsən.

---

## 1) Lokal işə salma (2 dəqiqə)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # açarları boş saxlaya bilərsən, demo işləyəcək
uvicorn app.main:app --reload --port 8000
```

Brauzerdə aç: **http://localhost:8000/docs** — Swagger UI ilə bütün 8
endpoint-i canlı test edə bilərsən (fetch-text, translate-text, fetch-images,
generate-tts, generate-video, upload-to-youtube, analytics, revenue).

> ⚠️ `generate-video` üçün `ffmpeg` sisteminizdə quraşdırılmış olmalıdır:
> - Mac: `brew install ffmpeg`
> - Ubuntu/Debian: `sudo apt install ffmpeg`
> - Windows: https://ffmpeg.org/download.html

---

## 2) Frontend-i backend-ə qoşmaq

`mahni_section6_complete.html` faylında hazırda bütün SECTION-lar `localStorage`
və ya brauzer-daxili simulyasiya ilə işləyir. Real backend-ə keçmək üçün hər
SECTION-un JS kodunda müvafiq `fetch()` çağırışını backend URL-inə yönəlt, məs:

```javascript
// Əvvəl (demo):
const analytics = ensureAnalyticsSeed(channelId);

// Sonra (real backend):
const res = await fetch(`${BACKEND_URL}/api/analytics/${channelId}`);
const analytics = await res.json();
```

Faylın başına bir dəyişən əlavə et:
```javascript
const BACKEND_URL = "https://sənin-render-linkin.onrender.com"; // deploy sonrası
```

Bunu istəsən mən edə bilərəm — hazır olanda "frontend-i backend-ə qoşaq" de.

---

## 3) Render.com-a Deploy

### A. Git-ə yüklə
```bash
cd backend
git init
git add .
git commit -m "SECTION 7: Backend kuruluşu"
git remote add origin <sənin-github-repo-linkin>
git push -u origin main
```

### B. Render Dashboard
1. https://dashboard.render.com → **New** → **Blueprint**
2. GitHub repo-nu seç (bu `backend/` qovluğu olan repo)
3. Render `render.yaml`-ı tapıb avtomatik quracaq:
   - 1 Web Service (Docker, ffmpeg daxil)
   - 1 Postgres verilənlər bazası (pulsuz tier)
4. **Environment** bölməsində boş qalan (sync: false) dəyişənləri doldur:
   - `PUBLIC_BASE_URL` → Render sənə verdiyi URL (məs. `https://auto-video-backend.onrender.com`)
   - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` (aşağıya bax)
   - `PEXELS_API_KEY` (istəyə görə)
5. **Deploy** düyməsinə bas. 3-5 dəqiqəyə canlı olacaq.
6. Yoxla: `https://<sənin-linkin>.onrender.com/health` → `{"status":"healthy"}`

> Pulsuz Render planı 15 dəqiqə istifadəsiz qalanda "yatır" — ilk sorğu 30-50
> saniyə gecikə bilər. Prodakşn üçün ödənişli plana keçmək tövsiyə olunur.

---

## 4) Real API açarlarının alınması (istəyə bağlı, addım-addım)

### 🔑 YouTube Data API + Analytics API (OAuth)
1. https://console.cloud.google.com → yeni layihə yarat
2. **APIs & Services → Library** → axtar və aktivləşdir:
   - `YouTube Data API v3`
   - `YouTube Analytics API`
3. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
   - Application type: **Web application**
   - Authorized redirect URI: `https://<sənin-linkin>.onrender.com/api/auth/youtube/callback`
4. Client ID/Secret-i `.env`-ə (və ya Render Environment-ə) yaz.
5. Hər kanal üçün admin `GET /api/auth/youtube/login?channel_id=1` linkinə
   daxil olub Google icazə verir → `refresh_token` avtomatik DB-də saxlanır.

### 🔑 AdSense (gəlir rəqəmləri)
AdSense Management API yalnız YouTube-un rəsmi monetizasiya təsdiqi olan
kanallar üçün işləyir. Açar alma addımları: https://developers.google.com/adsense/management
Açar olmadan tətbiq `estimate_revenue()` funksiyası ilə **təxmini** RPM/CPM
hesablamağa davam edir (SECTION 6-dakı frontend kalkulyator ilə eyni düstur).

### 🔑 Pexels (şəkillər, SECTION 2)
https://www.pexels.com/api/ → pulsuz qeydiyyat → açarı `.env`-ə yaz.
Açar yoxdursa placeholder şəkillər istifadə olunur.

### 🔑 TTS (SECTION 3)
Default: `gTTS` (pulsuz, açar lazım deyil, lakin Azərbaycan dilini birbaşa
dəstəkləmədiyi üçün türk dilinə fallback edir). Daha keyfiyyətli/Azərbaycan
dəstəkli səs üçün:
- **ElevenLabs** (`ELEVENLABS_API_KEY`) — ən yaxşı keyfiyyət, pullu
- **Azure Speech** (`AZURE_SPEECH_KEY` + `AZURE_SPEECH_REGION`) — Azərbaycan
  dilini rəsmi dəstəkləyir

---

## 5) Verilənlər bazası (Database)

Default: **SQLite** (`./app.db`, quraşdırma tələb etmir, lokal test üçün əladır).
Render-də `render.yaml` avtomatik **Postgres** DB yaradır və `DATABASE_URL`-i
bağlayır — kodda heç bir dəyişiklik lazım deyil (`SQLAlchemy` hər ikisini dəstəkləyir).

Cədvəllər (`app/models.py`):
- **channels** — SECTION 5-dəki kanal siyahısının server qarşılığı
- **video_jobs** — hər video-generasiya prosesinin izlənməsi (status, tərəqqi %)
- **analytics_snapshots** — SECTION 6-nın gündəlik tarixçəsi (server tərəfdə saxlanır)

---

## 6) Təhlükəsizlik qeydləri (prodakşna keçməzdən əvvəl)

- `oauth_refresh_token` sahəsi hazırda açıq mətn saxlanır — prodakşnda
  **şifrələnməlidir** (məs. `cryptography.fernet.Fernet`). Nümunə:
  ```python
  from cryptography.fernet import Fernet
  # .env-ə FERNET_KEY əlavə et, Channel.oauth_refresh_token-i yazmadan/oxumadan
  # əvvəl encrypt/decrypt et.
  ```
- `ALLOWED_ORIGINS=*` yalnız inkişaf üçündür — prodakşnda öz frontend domenini yaz.
- YouTube-a yükləmə hazırda `privacyStatus: private` ilə gedir (təhlükəsiz default) —
  ictimai etmək istəsən `app/services/youtube_service.py`-də dəyiş.

---

## 📊 STATUS: SECTION 7 TAMAMLANDI ✅

Endpoint-lərin hamısı yazılıb, sintaksis yoxlanılıb, demo/real rejim keçidi
hər servisdə var (açar yoxdursa demo, varsa avtomatik real). Sıradakı addım:
**SECTION 8+ (Finishing)** — redaktor rejimi, keşləmə, error/retry, user guide.
