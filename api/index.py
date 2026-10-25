"""Vercel Serverless Function entrypoint for InfluenceMatch API."""
import os
import sys
from pathlib import Path
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

# Ensure src/ is on the Python module search path
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
PUBLIC_DIR = BASE_DIR / "public"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Ensure DATA_DIR is explicitly configured
os.environ.setdefault("DATA_DIR", str(DATA_DIR))
os.environ.setdefault("INFLUENCEMATCH_DATA_BACKEND", "files")

from influencematch.api import app as base_app

app = FastAPI(
    title="InfluenceMatch API",
    version="0.2.0",
    description="Authentic Instagram Influencer Recommendation System backed by provenance-verified data",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# Support both /api/xxx and /xxx routes seamlessly on Vercel
app.include_router(base_app.router, prefix="/api")
app.include_router(base_app.router)

# Mount static frontend for unified local runs and edge fallbacks
if PUBLIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="public")
