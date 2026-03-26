"""
cleaner.py — Transcript cleaning and smart chunking

Cleans raw YouTube transcripts and prepares them for the LLM:
  - Removes caption artefacts ([Music], [Applause], etc.)
  - Merges short fragmented segments into readable sentences
  - Formats timestamps for inclusion in the LLM prompt
  - Chunks long transcripts to fit within context window
"""

import os
import re
import logging
from .extractor import TranscriptEntry, format_timestamp

logger = logging.getLogger(__name__)

MAX_TRANSCRIPT_CHARS = int(os.getenv("MAX_TRANSCRIPT_CHARS", 12000))


def clean_and_format(entries: list[TranscriptEntry]) -> str:
    """
    Convert transcript entries into a clean, timestamped text block
    suitable for passing to the LLM.

    Format:
        [0:00] First sentence of the video here.
        [1:23] Next idea or section starts here.

    A timestamp is inserted at natural breakpoints (every ~30 seconds)
    rather than every single caption segment, which would be noisy.
    """
    if not entries:
        return ""

    lines = []
    last_timestamp_at = -30.0  # force a timestamp on the first line

    current_text = []
    current_start = entries[0].start

    for entry in entries:
        text = _clean_segment(entry.text)
        if not text:
            continue

        # Add timestamp marker every ~30 seconds
        if entry.start - last_timestamp_at >= 30.0:
            if current_text:
                ts = format_timestamp(current_start)
                lines.append(f"[{ts}] {' '.join(current_text)}")
                current_text = []

            current_start = entry.start
            last_timestamp_at = entry.start

        current_text.append(text)

    # Flush remaining text
    if current_text:
        ts = format_timestamp(current_start)
        lines.append(f"[{ts}] {' '.join(current_text)}")

    return "\n".join(lines)


def chunk_transcript(formatted: str) -> list[str]:
    """
    Split a long transcript into overlapping chunks if it exceeds
    MAX_TRANSCRIPT_CHARS. Each chunk keeps ~200 chars of overlap
    from the previous chunk so context is preserved across boundaries.

    For short transcripts, returns a single-element list.
    """
    if len(formatted) <= MAX_TRANSCRIPT_CHARS:
        logger.info(f"Transcript fits in one chunk ({len(formatted)} chars)")
        return [formatted]

    lines = formatted.split("\n")
    chunks = []
    current_chunk = []
    current_len = 0
    overlap_lines = []

    for line in lines:
        line_len = len(line) + 1
        if current_len + line_len > MAX_TRANSCRIPT_CHARS and current_chunk:
            chunks.append("\n".join(current_chunk))
            # Keep last few lines as overlap for context
            overlap_lines = current_chunk[-5:]
            current_chunk = overlap_lines.copy()
            current_len = sum(len(l) + 1 for l in current_chunk)

        current_chunk.append(line)
        current_len += line_len

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    logger.info(f"Split transcript into {len(chunks)} chunks (max {MAX_TRANSCRIPT_CHARS} chars each)")
    return chunks


def _clean_segment(text: str) -> str:
    """Clean a single transcript segment."""
    # Remove caption artefacts
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\(.*?\)", "", text)

    # Remove music notes and special chars
    text = re.sub(r"[♪♫]", "", text)

    # Normalise whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Skip very short fragments (single letters, numbers only)
    if len(text) < 3:
        return ""

    return text


def build_prompt_transcript(entries: list[TranscriptEntry]) -> tuple[str, bool]:
    """
    Prepare transcript for the LLM prompt.
    Returns (transcript_text, was_chunked).
    If the transcript is too long, returns the first chunk with a note.
    """
    formatted = clean_and_format(entries)
    chunks = chunk_transcript(formatted)

    if len(chunks) == 1:
        return formatted, False

    # For summarisation, use the full transcript joined with section markers
    # This gives better overall summaries than using only the first chunk
    combined = "\n\n[--- SECTION BREAK ---]\n\n".join(chunks)

    # If still too long, trim intelligently — keep beginning and end
    max_combined = MAX_TRANSCRIPT_CHARS * 3
    if len(combined) > max_combined:
        half = max_combined // 2
        combined = (
            combined[:half]
            + "\n\n[... middle section omitted for length ...]\n\n"
            + combined[-half:]
        )

    return combined, True
