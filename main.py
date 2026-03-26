import os
import time
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv

from extractor import fetch_transcript, extract_video_id
from cleaner import build_prompt_transcript
from summarizer import summarize

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

app = FastAPI(
    title="YTSummarize AI",
    description="Paste a YouTube URL. Get a structured summary with key points and timestamps.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SummarizeRequest(BaseModel):
    url: str
    language: str = "en"

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, v):
        if "youtube.com" not in v and "youtu.be" not in v:
            raise ValueError("URL must be a YouTube link (youtube.com or youtu.be)")
        return v.strip()


@app.get("/", tags=["Health"])
def root():
    return {"service": "YTSummarize AI", "status": "ok", "docs": "/docs"}


@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "healthy"}


@app.post("/api/summarize", tags=["Summarize"])
def summarize_video(request: SummarizeRequest):
    start = time.time()

    try:
        video_id = extract_video_id(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        transcript_result = fetch_transcript(request.url, language=request.language)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    transcript_text, was_chunked = build_prompt_transcript(transcript_result.entries)

    if not transcript_text.strip():
        raise HTTPException(status_code=422, detail="Transcript appears to be empty after cleaning.")

    try:
        summary = summarize(transcript_text, video_id=video_id, was_chunked=was_chunked)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

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
