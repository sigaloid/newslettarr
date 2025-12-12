# Newslettarr

Generates HTML newsletters of recently added Jellyfin media.

## Features

- Fetches recent Movies and TV Series from Jellyfin.
- Groups items by week (configurable).
- Optional AI-generated headlines via Ollama.
- Generates mobile-friendly HTML files.

## Setup

1. Copy `.env.example` to `.env`.
2. Configure `JELLYFIN_HOST`, `JELLYFIN_USERNAME`, `JELLYFIN_PASSWORD`.
3. Optional: Configure `OLLAMA_HOST` for AI headlines.

## Running Locally

```bash
pip install -r requirements.txt
python run.py
```

Access at http://localhost:5000

## Docker

Build and run with Docker Compose:

```bash
docker compose up -d --build
```

Newsletters are saved to `./newsletters` (mounted volume, or just rebuild on restart).
