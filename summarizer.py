"""
summarizer.py — GPT-4o powered video summarization

Takes a cleaned, timestamped transcript and produces a fully structured
summary using carefully engineered prompts.

Output sections:
  - TL;DR          : 2–3 sentence overview
  - Key takeaways  : 5–8 bullet points
  - Timestamps     : important moments with labels
  - Chapters       : major sections with summaries
  - Notable quotes : direct quotes worth highlighting
  - Tags           : auto-detected topic tags

Prompt engineering principles applied:
  1. Role priming       — "You are an expert content analyst..."
  2. Hard constraints   — exact counts, word limits
  3. JSON schema        — structured, parseable output every time
  4. Grounding          — "Based ONLY on the transcript provided"
  5. Timestamp fidelity — "Use ONLY timestamps that appear in [brackets]"
  6. Low temperature    — 0.2 for consistent, factual output
"""

import os
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

LLM_MODEL  = os.getenv("LLM_MODEL", "gpt-4o")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 2000))

client = OpenAI()


def summarize(transcript: str, video_id: str = "", was_chunked: bool = False) -> dict:
    """
    Generate a full structured summary from a timestamped transcript.

    Args:
        transcript:   Cleaned, timestamped transcript text
        video_id:     YouTube video ID (for building watch URLs)
        was_chunked:  Whether the transcript was split (affects prompt)

    Returns:
        Structured summary dict
    """
    prompt = _build_prompt(transcript, video_id, was_chunked)
    logger.info(f"Sending {len(transcript)} chars to {LLM_MODEL}...")

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=MAX_TOKENS,
        temperature=0.2,  # low = consistent, factual output
    )

    raw = response.choices[0].message.content.strip()
    return _parse_response(raw)


def _build_prompt(transcript: str, video_id: str, was_chunked: bool) -> str:
    """
    Build the summarization prompt.

    Key design decisions:
    - Role priming sets the model as an expert analyst, not a generic assistant
    - "Based ONLY on the transcript" prevents hallucination
    - Timestamp instruction is critical: only use timestamps from [brackets] in the text
    - JSON schema is fully specified so output is always parseable
    - Counts are explicit (exactly 5-8 takeaways, exactly 5-8 timestamps)
    - Low token temperature instruction embedded in framing
    """
    chunk_note = (
        "\nNote: This is a long video. The transcript may be divided into sections. "
        "Summarise the video as a whole, not just one section.\n"
        if was_chunked else ""
    )

    watch_base = f"https://www.youtube.com/watch?v={video_id}&t=" if video_id else ""

    return f"""You are an expert content analyst who creates structured, useful video summaries.

Based ONLY on the transcript provided below, generate a complete structured summary.

CRITICAL RULES:
- Use ONLY information present in the transcript. Do not add outside knowledge.
- For timestamps: use ONLY timestamps that appear in [brackets] in the transcript (e.g. [2:34]).
  Never invent or estimate timestamps. If a timestamp is not in the transcript, skip it.
- Quotes must be near-verbatim from the transcript. Do not paraphrase as quotes.
{chunk_note}
Return ONLY valid JSON — no markdown backticks, no preamble, no extra text.

JSON schema to follow exactly:
{{
  "tldr": "2-3 sentence plain English overview of the entire video",
  "key_takeaways": [
    "First key insight or point (1-2 sentences)",
    "Second key insight or point"
  ],
  "timestamps": [
    {{
      "time": "0:00",
      "seconds": 0,
      "label": "Brief description of what happens at this moment",
      "url": "{watch_base}0"
    }}
  ],
  "chapters": [
    {{
      "title": "Chapter or section name",
      "start": "0:00",
      "summary": "1-2 sentence description of what this section covers"
    }}
  ],
  "notable_quotes": [
    "A direct quote from the speaker worth highlighting"
  ],
  "tags": ["topic1", "topic2", "topic3"]
}}

Requirements per section:
- tldr: exactly 2-3 sentences, plain language, no jargon unless necessary
- key_takeaways: 5-8 items, each 1-2 sentences, start with a verb or noun (not "The")
- timestamps: 5-8 items, use ONLY timestamps from the [brackets] in the transcript
- chapters: 3-6 items covering the major sections of the video
- notable_quotes: 2-4 items, only if clearly quotable — omit section if no good quotes exist
- tags: 4-8 lowercase single or two-word topic tags

TRANSCRIPT:
{transcript}"""


def _parse_response(raw: str) -> dict:
    """Parse the LLM JSON response, with fallback cleanup."""
    # Strip markdown fences if present (defensive — shouldn't happen at temp 0.2)
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}\nRaw (first 500 chars): {raw[:500]}")
        raise ValueError(f"LLM returned invalid JSON: {e}")

    # Validate and fill missing keys with safe defaults
    defaults = {
        "tldr": "",
        "key_takeaways": [],
        "timestamps": [],
        "chapters": [],
        "notable_quotes": [],
        "tags": [],
    }
    for key, default in defaults.items():
        if key not in data:
            logger.warning(f"LLM response missing key: '{key}', using default")
            data[key] = default

    # Ensure seconds field on timestamps
    for ts in data.get("timestamps", []):
        if "seconds" not in ts:
            ts["seconds"] = _time_to_seconds(ts.get("time", "0:00"))

    return data


def _time_to_seconds(time_str: str) -> int:
    """Convert 'M:SS' or 'H:MM:SS' to integer seconds."""
    try:
        parts = list(map(int, time_str.split(":")))
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except Exception:
        pass
    return 0
