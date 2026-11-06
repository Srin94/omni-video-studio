# Hosting omni-video-studio for free

The pipeline has three parts with very different appetites, so they go to three
different free homes instead of one box:

| Part | What it does | Free home |
| --- | --- | --- |
| **Rendering** (`video-engine`) | Remotion + headless Chrome, CPU-heavy, runs for minutes | **GitHub Actions** |
| **Authoring API** (`agent-backend`) | trends, prompt relay, schema validation — light HTTP | **Render / Fly.io / HF Space** (Docker) |
| **Studio UI** (`web-studio`) | static Vite/React dashboard | **Cloudflare Pages / GitHub Pages** |

The human-in-the-loop part (pasting the master prompt into Gemini/Claude in your
browser, the Telegram approval tap) needs no hosting — it's just you.

---

## 1. Rendering → GitHub Actions (the heavy part, free)

Already wired up in [`.github/workflows/render.yml`](.github/workflows/render.yml).

- Push a payload to [`render-jobs/`](render-jobs/) (see its README), or run
  **Actions → Render video → Run workflow**.
- The job runs the real pipeline with Telegram + YouTube skipped and uploads
  `final_video.mp4` as a build artifact you download from the run.

**Minutes:** Actions is **unlimited on a public repo**. On a private repo the
free plan gives **2,000 minutes/month** — a ~90s portrait Short renders in
roughly 12–18 min, so that's ~100+ Shorts/month. Make the repo public if you
want it truly uncapped.

No secrets are needed for a render (it's `--dry-run --skip-approval`). Only add
repo **Secrets** (Settings → Secrets → Actions) if you later extend the workflow
to publish — `TELEGRAM_BOT_TOKEN`, `YOUTUBE_*`, etc. Never commit a `.env`.

## 2. Authoring API → Render.com (or Fly.io / Hugging Face Space)

Build context is the **repo root** (the Dockerfile copies `agent-backend/`):

```bash
docker build -f agent-backend/Dockerfile -t omni-api .
docker run -p 8000:8000 omni-api
```

**Render.com (simplest):** New → Web Service → point at this repo →
Runtime *Docker*, Dockerfile path `agent-backend/Dockerfile`, Docker context `.`
(root). It injects `$PORT` automatically. Set env var `CORS_ORIGINS` to your
deployed studio URL so the browser can call it.

The image is intentionally small — no Node, no Chrome — because rendering lives
in Actions. Free web services on Render sleep when idle and wake on the next
request; fine for a personal tool.

## 3. Studio UI → Cloudflare Pages / GitHub Pages (optional)

```bash
cd web-studio && npm ci && npm run build   # outputs dist/
```

Deploy `web-studio/dist` as a static site. Set the build-time env var
`VITE_API_BASE` to your authoring API URL (e.g.
`https://omni-api.onrender.com`) so the UI calls the hosted backend instead of a
local proxy.

---

## End-to-end, once hosted

1. Open the hosted studio → pick a topic → copy the master prompt.
2. Paste it into Gemini/Claude in your browser → copy the JSON back →
   *Validate Schema*.
3. Save that JSON to `render-jobs/<name>.json`, commit, push.
4. Download the rendered `final_video.mp4` from the Actions run.
5. (Optional) publish it yourself, or wire the YouTube step into a second
   workflow gated on your Telegram approval.
