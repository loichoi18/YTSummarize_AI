# Prompt Engineering — YTSummarize AI

Every LLM call in this project uses a single carefully engineered prompt.
This document explains every design decision and what was learned through iteration.

---

## The Core Challenge

YouTube transcripts are messy. They contain:
- Fragmented sentences split across caption segments
- No punctuation in auto-generated captions
- Filler words, repeated phrases, speaker artefacts
- Timestamps that don't align with topic boundaries

The prompt must produce structured, useful output from this noisy input.

---

## The Prompt — Design Decisions

### 1. Role Priming
```
You are an expert content analyst who creates structured, useful video summaries.
```
Setting the model as a "content analyst" rather than a general assistant anchors
the output style. It produces more concise, structured summaries versus long
explanations when asked generically.

### 2. Grounding Constraint
```
Based ONLY on the transcript provided below, generate a complete structured summary.
Do not add outside knowledge.
```
Without this, GPT-4o adds context from its training data. A video about Python
gets summaries mentioning things the speaker never said. The "ONLY" constraint
fixes this.

### 3. Timestamp Fidelity (most important constraint)
```
For timestamps: use ONLY timestamps that appear in [brackets] in the transcript.
Never invent or estimate timestamps.
```
Without this, the model hallucinates plausible-sounding timestamps.
"3:45 — The speaker discusses X" sounds credible but is completely fabricated
if 3:45 doesn't exist in the transcript. This constraint eliminates hallucinated
timestamps entirely.

### 4. JSON Schema Enforcement
Providing the exact JSON schema with field names and types ensures:
- Consistent key names across every response (`key_takeaways` not `keyTakeaways`)
- Parseable output every time (no markdown fences, no preamble)
- Frontend can render reliably without defensive parsing

### 5. Count Constraints
```
key_takeaways: 5-8 items
timestamps: 5-8 items
chapters: 3-6 items
```
Without counts, output varies wildly. Short videos get 2 takeaways,
long videos get 20. Explicit ranges create consistency at scale.

### 6. Temperature: 0.2
Lower than typical (0.7) because:
- Summaries must be factual and grounded, not creative
- Consistent format is more important than varied phrasing
- Timestamp extraction is quasi-extraction, not generation

---

## What Failed in Early Iterations

| Problem | Cause | Fix |
|---|---|---|
| Hallucinated timestamps | No constraint on timestamp source | Added "use ONLY timestamps from [brackets]" |
| Inconsistent JSON keys | No schema specified | Added exact schema with field names |
| Outside knowledge added | No grounding constraint | Added "Based ONLY on transcript" |
| Too many/few takeaways | No count given | Added explicit range (5-8) |
| Markdown fences in output | Default model behaviour | Added "no markdown backticks, no preamble" |
| Empty sections for short videos | Model skips optional sections | Added fallback defaults in parser |

---

*Maintained by Ba Dung Luong — Bachelor of Artificial Intelligence, UTS*
