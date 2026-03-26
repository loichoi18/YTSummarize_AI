"""
extractor.py — YouTube transcript extraction
Updated for youtube-transcript-api v1.x
"""

import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TranscriptEntry:
    text: str
    start: float
    duration: float


@dataclass
class TranscriptResult:
    video_id: str
    language: str
    entries: list

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
    patterns = [
        r"(?:v=)([a-zA-Z0-9_-]{11})",
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:embed/)([a-zA-Z0-9_-]{11})",
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
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        raise ImportError("Install youtube-transcript-api: pip install youtube-transcript-api")

    video_id = extract_video_id(url)
    logger.info(f"Fetching transcript for video: {video_id}")

    try:
        # ── New API (v1.x) ──────────────────────────────────────────
        # YouTubeTranscriptApi is now instantiated, not used as a static class
        ytt = YouTubeTranscriptApi()

        try:
            # Try to get transcript in requested language first
            transcript_list = ytt.list(video_id)
            try:
                transcript = transcript_list.find_transcript([language])
            except Exception:
                try:
                    transcript = transcript_list.find_generated_transcript(["en"])
                except Exception:
                    # Fall back to whatever is available
                    transcript = next(iter(transcript_list))

            fetched = transcript.fetch()
            used_language = transcript.language_code

        except Exception:
            # Final fallback — fetch directly
            fetched = ytt.fetch(video_id)
            used_language = language

        # Handle both old FetchedTranscript object and plain list formats
        entries = []
        items = list(fetched)
        for item in items:
            # Support both dict-style and object-style access
            if hasattr(item, 'text'):
                text = item.text
                start = item.start
                duration = getattr(item, 'duration', 0.0)
            else:
                text = item.get("text", "")
                start = item.get("start", 0.0)
                duration = item.get("duration", 0.0)

            text = str(text).strip()
            if text:
                entries.append(TranscriptEntry(text=text, start=float(start), duration=float(duration)))

        if not entries:
            raise ValueError("Transcript was empty after processing.")

        result = TranscriptResult(
            video_id=video_id,
            language=used_language,
            entries=entries,
        )

        logger.info(f"Transcript fetched: {len(entries)} segments, {result.word_count} words")
        return result

    except ValueError:
        raise
    except Exception as e:
        error_msg = str(e)
        if "disabled" in error_msg.lower():
            raise ValueError("This video has captions disabled.")
        elif "no transcript" in error_msg.lower():
            raise ValueError(f"No transcript found for video {video_id}.")
        else:
            raise ValueError(f"Failed to fetch transcript: {error_msg}")


def format_timestamp(seconds: float) -> str:
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
