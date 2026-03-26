# 🎬 YTSummarize AI
### *Paste a YouTube URL. Get a structured summary with key points and timestamps.*

> An AI-powered tool that extracts transcripts from any YouTube video and uses GPT-4o to produce structured, timestamped summaries — in seconds.

**Ba Dung Luong — Bachelor of Artificial Intelligence, UTS**

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.103-green)](https://fastapi.tiangolo.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-black)](https://openai.com)

---

## 🎬 Demo

```
INPUT:  https://www.youtube.com/watch?v=dQw4w9WgXcQ

OUTPUT:
  📋 TL;DR Summary       — 3-sentence overview
  🧠 Key Takeaways       — 5–8 bullet points
  🕐 Timestamped Moments — clickable timestamps with what happens at each point
  📚 Chapter Breakdown   — major sections of the video
  💬 Notable Quotes      — direct quotes worth remembering
  🏷️  Tags & Topics       — auto-detected subject tags
```

---

## 🤔 The Problem

YouTube videos are long. Finding the key insight buried in a 45-minute talk,
checking if a tutorial covers what you need, or reviewing a lecture you already
watched — all of this wastes time.

YTSummarize AI solves this by giving you the structure of any video before
(or instead of) watching it.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    USER PASTES URL                           │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│               BACKEND — FastAPI (Python)                     │
│                                                              │
│  1. EXTRACTOR   →  youtube-transcript-api fetches transcript │
│  2. CLEANER     →  normalise timestamps, remove filler       │
│  3. CHUNKER     →  split long transcripts for context window │
│  4. SUMMARIZER  →  GPT-4o with engineered prompt             │
│  5. FORMATTER   →  structure output as clean JSON            │
└──────────────────────┬───────────────────────────────────────┘
                       │ JSON
                       ▼
┌──────────────────────────────────────────────────────────────┐
│               FRONTEND — HTML + CSS + JS                     │
│   URL input → Loading state → Structured summary display     │
└──────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
yt-summarizer/
│
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   └── core/
│       ├── extractor.py         # YouTube transcript extraction
│       ├── cleaner.py           # Transcript cleaning & chunking
│       └── summarizer.py        # OpenAI GPT-4o summarization
│
├── frontend/
│   └── index.html               # Single-file frontend (HTML + CSS + JS)
│
├── docs/
│   ├── HOW_IT_WORKS.md
│   └── PROMPT_ENGINEERING.md
│
├── examples/
│   └── sample_output.json       # Example API response
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone and install
```bash
git clone https://github.com/loichoi18/yt-summarizer.git
cd yt-summarizer
pip install -r requirements.txt
```

### 2. Add your OpenAI API key
```bash
cp .env.example .env
# Edit .env: OPENAI_API_KEY=sk-...
```

### 3. Start the backend
```bash
uvicorn backend.main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

### 4. Open the frontend
```bash
# Just open frontend/index.html in your browser
# Or serve it:
cd frontend && python -m http.server 3000
# Open: http://localhost:3000
```

---

## 🔌 API

### `POST /api/summarize`
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "language": "en"
}
```

**Response:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "title": "Video Title",
  "duration_seconds": 3240,
  "tldr": "A 3-sentence overview of the entire video.",
  "key_takeaways": [
    "First major insight from the video",
    "Second key point worth knowing"
  ],
  "timestamps": [
    { "time": "0:00", "seconds": 0,   "label": "Introduction" },
    { "time": "2:34", "seconds": 154, "label": "First major topic explained" }
  ],
  "chapters": [
    { "title": "Chapter name", "start": "0:00", "summary": "What this section covers" }
  ],
  "notable_quotes": [
    "A direct quote worth highlighting from the speaker"
  ],
  "tags": ["machine learning", "python", "tutorial"],
  "word_count": 4821,
  "processing_time_secs": 8.3
}
```

### `GET /api/health`
Returns service status.

---

## ⚙️ How It Works

1. **Transcript extraction** — `youtube-transcript-api` fetches the auto-generated or manual captions directly from YouTube. No scraping, no browser automation.

2. **Cleaning** — Removes filler words, normalises whitespace, and formats timestamps into readable `MM:SS` format.

3. **Chunking** — Long transcripts (1hr+ videos) are split into overlapping chunks to stay within GPT-4o's context window.

4. **Summarization** — A structured prompt asks GPT-4o to produce each output section (TL;DR, key points, timestamps, etc.) in strict JSON format.

5. **Response** — The structured JSON is returned to the frontend and rendered into a clean, readable summary.

---

## 🧩 Related Projects

**🎓 LectureForge AI** — Converts lecture files into full LMS-ready learning modules using Whisper + RAG + GPT-4o.
👉 [github.com/loichoi18/Lecture_Forge_AI](https://github.com/loichoi18/Lecture_Forge_AI)

**🛡️ Explainable XDR-SIEM** — Cybersecurity AI platform with ML detection, SHAP explainability, and causal attack graphs.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Transcript | youtube-transcript-api |
| LLM | GPT-4o |
| Backend | FastAPI + Uvicorn |
| Frontend | HTML + CSS + Vanilla JS |
| Data Validation | Pydantic v2 |

---

## 👤 About

**Ba Dung Luong** — Bachelor of Artificial Intelligence, UTS

📧 BaDung.Luong@student.uts.edu.au
🔗 [linkedin.com/in/badunsyd](https://www.linkedin.com/in/badunsyd/)
🐙 [github.com/loichoi18](https://github.com/loichoi18)
🌐 [loichoi18.github.io](https://loichoi18.github.io)
