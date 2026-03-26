"""
extractor.py — YouTube transcript extraction

Fetches the transcript (captions) from any YouTube video
using the youtube-transcript-api library.

Handles:
  - Standard youtube.com/watch?v=ID URLs
  - Shortened youtu.be/ID URLs
  - URLs with extra parameters (&t=, &list=, etc.)
  - Videos with manual or auto-generated captions
  - Language fallback (tries requested language, falls back to English)
"""

import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TranscriptEntry:
    text: str
    start: float   # seconds from video start
    duration: float


@dataclass
class TranscriptResult:
    video_id: str
    language: str
    entries: list[TranscriptEntry]

    @property
    def full_text(self) -> str:
        return " ".join(e.text for e in self.entries)

    @property
    def duration_seconds(self) -> float:
        if not self.entries:
            return 0.0
        last = self.entries[-1]
        return last.start + last.duration

    @property
    def word_count(self) -> int:
        return len(self.full_text.split())


def extract_video_id(url: str) -> str:
    """
    Extract the YouTube video ID from any YouTube URL format.

    Supports:
      https://www.youtube.com/watch?v=dQw4w9WgXcQ
      https://youtu.be/dQw4w9WgXcQ
      https://www.youtube.com/embed/dQw4w9WgXcQ
      https://youtube.com/watch?v=dQw4w9WgXcQ&t=30s
    """
    patterns = [
        r"(?:v=)([a-zA-Z0-9_-]{11})",       # ?v=ID
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})", # youtu.be/ID
        r"(?:embed/)([a-zA-Z0-9_-]{11})",     # /embed/ID
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(
        f"Could not extract video ID from URL: {url}\n"
        "Please use a standard YouTube URL like: https://www.youtube.com/watch?v=VIDEO_ID"
    )


def fetch_transcript(url: str, language: str = "en") -> TranscriptResult:
    """
    Fetch the full transcript for a YouTube video.

    Args:
        url:      YouTube video URL
        language: Preferred language code (e.g. 'en', 'fr', 'es')

    Returns:
        TranscriptResult with all entries and metadata

    Raises:
        ValueError: If URL is invalid or video has no captions
    """
    try:
        from youtube_transcript_api import (
            YouTubeTranscriptApi,
            TranscriptsDisabled,
            NoTranscriptFound,
        )
    except ImportError:
        raise ImportError("Install youtube-transcript-api: pip install youtube-transcript-api")

    video_id = extract_video_id(url)
    logger.info(f"Fetching transcript for video: {video_id} (language: {language})")

    try:
        # Try requested language first, then fall back to any available
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            try:
                transcript = transcript_list.find_transcript([language])
            except NoTranscriptFound:
                # Fall back to auto-generated English, then any available
                logger.warning(f"No '{language}' transcript found, trying fallbacks...")
                try:
                    transcript = transcript_list.find_generated_transcript(["en"])
                except NoTranscriptFound:
                    transcript = next(iter(transcript_list))
            
            raw = transcript.fetch()
            used_language = transcript.language_code

        except Exception:
            # Simplest fallback — just get whatever is available
            raw = YouTubeTranscriptApi.get_transcript(video_id)
            used_language = language

        entries = [
            TranscriptEntry(
                text=item["text"].strip(),
                start=item["start"],
                duration=item.get("duration", 0.0),
            )
            for item in raw
            if item.get("text", "").strip()
        ]

        result = TranscriptResult(
            video_id=video_id,
            language=used_language,
            entries=entries,
        )

        logger.info(
            f"Transcript fetched: {len(entries)} segments, "
            f"{result.word_count} words, "
            f"{result.duration_seconds:.0f}s duration"
        )
        return result

    except TranscriptsDisabled:
        raise ValueError(
            "This video has captions disabled. "
            "YTSummarize AI requires videos with available captions."
        )
    except NoTranscriptFound:
        raise ValueError(
            f"No transcript found for video {video_id}. "
            "The video may not have captions enabled."
        )
    except Exception as e:
        raise ValueError(f"Failed to fetch transcript: {str(e)}")


def format_timestamp(seconds: float) -> str:
    """Convert float seconds to MM:SS or HH:MM:SS string."""
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
