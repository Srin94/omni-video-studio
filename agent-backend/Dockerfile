# ---------------------------------------------------------------------------
# Authoring API for omni-video-studio (trends + prompt relay + schema validate).
#
# The heavy Remotion rendering deliberately does NOT run here — it runs in
# GitHub Actions (.github/workflows/render.yml). That keeps this image small
# (no Node, no headless Chrome) so it fits any free tier:
#   Render.com (free web service), Fly.io (free allowance), or a
#   Hugging Face Space (Docker SDK).
#
# Build from the REPO ROOT so the build context can see agent-backend/:
#   docker build -f agent-backend/Dockerfile -t omni-api .
#   docker run -p 8000:8000 omni-api
# ---------------------------------------------------------------------------
FROM python:3.12-slim

# ffmpeg is only needed if you later enable the audio endpoints; harmless here.
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY agent-backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY agent-backend/ ./

# Hosts like Render / Fly inject $PORT; default to 8000 for local runs.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}"]
