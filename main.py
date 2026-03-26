"""
main.py — YTSummarize AI FastAPI backend

Run with:
    uvicorn backend.main:app --reload --port 8000

Interactive API docs:
    http://localhost:8000/docs
"""
from backend.main import app
import time
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv

from .core.extractor import fetch_transcript, extract_video_id
from .core.cleaner import build_prompt_transcript
from .core.summarizer import summarize

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

app = FastAPI(
    title="YTSummarize AI",
    description="Paste a YouTube URL. Get a structured summary with key points and timestamps.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # open for local frontend dev
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────────────

class SummarizeRequest(BaseModel):
    url: str
    language: str = "en"

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, v):
        if "youtube.com" not in v and "youtu.be" not in v:
            raise ValueError("URL must be a YouTube link (youtube.com or youtu.be)")
        return v.strip()


# ── Routes ────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "service": "YTSummarize AI",
        "status":  "ok",
        "docs":    "/docs",
    }


@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "healthy"}


@app.post("/api/summarize", tags=["Summarize"])
def summarize_video(request: SummarizeRequest):
    """
    Summarize a YouTube video from its URL.

    Steps:
      1. Extract video ID from URL
      2. Fetch transcript via youtube-transcript-api
      3. Clean and format transcript with timestamps
      4. Send to GPT-4o for structured summarization
      5. Return full summary as JSON

    Takes ~5–15 seconds depending on video length.
    """
    start = time.time()

    # Step 1 — Extract video ID
    try:
        video_id = extract_video_id(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Step 2 — Fetch transcript
    try:
        transcript_result = fetch_transcript(request.url, language=request.language)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Step 3 — Clean and prepare for LLM
    transcript_text, was_chunked = build_prompt_transcript(transcript_result.entries)

    if not transcript_text.strip():
        raise HTTPException(status_code=422, detail="Transcript appears to be empty after cleaning.")

    # Step 4 — Summarize with GPT-4o
    try:
        summary = summarize(transcript_text, video_id=video_id, was_chunked=was_chunked)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    # Step 5 — Return enriched response
    elapsed = round(time.time() - start, 2)

    return {
        "video_id":             video_id,
        "url":                  request.url,
        "watch_url":            f"https://www.youtube.com/watch?v={video_id}",
        "duration_seconds":     round(transcript_result.duration_seconds),
        "word_count":           transcript_result.word_count,
        "language":             transcript_result.language,
        "processing_time_secs": elapsed,
        **summary,
    }
