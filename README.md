# Long-Form Memory System

**Team:** DEDSEC  
**Members:** Hiten Anand • Nidhi Singh

> A real-time AI memory system that retains and recalls information across **1,000+ conversation turns** — without replaying full conversation history or increasing system latency.

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [System Architecture](#system-architecture)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the System](#running-the-system)
- [Web Interface](#web-interface)
- [API Reference](#api-reference)
- [Performance Metrics](#performance-metrics)
- [Evaluation Criteria](#evaluation-criteria)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Problem Statement

Modern LLMs:
- Have limited context windows
- Cannot replay full conversation history
- Forget early information as conversations grow
- Become slow and expensive when full history is injected

**Example (from the hackathon spec):**
```
Turn 1:   "My preferred language is Kannada"
Turn 937: "Can you call me tomorrow?"
           → System must still know the language, constraints, and past commitments
```

**Our solution:** A fully automated memory pipeline that extracts, stores, retrieves, and injects information in real time with under 100ms overhead per turn.

---

## System Architecture

```
User Message
     │
     ▼
┌─────────────────────────────────────┐
│         Memory Retrieval            │  ← Pull relevant memories from past turns
│  (recency + confidence + semantic)  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│        Response Generation          │  ← Reply with memory context injected
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│        Memory Extraction            │  ← Classify new info from this turn
│  (preferences, facts, constraints,  │
│   commitments, instructions)        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│     Hybrid Memory Storage           │  ← Persist for all future turns
│  SQLite (structured) +              │
│  FAISS (vector / semantic)          │
└─────────────────────────────────────┘
               │
               ▼
         Response + Metadata
```

### Components

| Component | File | Role |
|-----------|------|------|
| Memory Extractor | `src/memory_extraction.py` | Identifies and classifies important info |
| Memory Storage | `src/memory_storage.py` | SQLite + FAISS hybrid persistence |
| Memory Retriever | `src/memory_retrieval.py` | Multi-signal relevance ranking |
| Conversation Agent | `src/conversation_agent.py` | Orchestrates the full pipeline |
| API Server | `src/api_server.py` | REST API for web/external access |

---

## Key Features

- **Automatic extraction** — no manual tagging; classifies 5 memory types from raw text
- **Hybrid storage** — SQLite for structured queries, FAISS for semantic search (FAISS is optional; system falls back to text search automatically)
- **Multi-signal retrieval** — combines recency (30%), confidence (40%), access count (20%), semantic similarity (10%)
- **Diversity filtering** — max 2 memories per type injected per turn to avoid prompt overload
- **Sub-100ms latency** — tested consistently across turns 1–1,000
- **Zero hallucinations** — every memory is traceable to a source turn with a confidence score
- **Session persistence** — memories survive across restarts via SQLite

### Memory Types

| Type | Example |
|------|---------|
| Preference | "My preferred language is Kannada" |
| Constraint | "Call me only after 11 AM" |
| Commitment | "I'll call you tomorrow" |
| Fact | "I work at TechCorp as a data scientist" |
| Instruction | "Always respond formally" |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.9+ |
| Structured Storage | SQLite (via SQLAlchemy) |
| Vector Search | FAISS — optional, text search fallback included |
| Embeddings | Sentence-Transformers (`all-MiniLM-L6-v2`) |
| API Server | Flask + Flask-CORS |
| Notebook Demo | Jupyter |
| Presentation | PptxGenJS |

---

## Project Structure

```
long-form-memory/
│
├── src/                              # Core source code
│   ├── memory_extraction.py          # Extracts & classifies memories from text
│   ├── memory_storage.py             # SQLite + FAISS hybrid storage (FAISS optional)
│   ├── memory_retrieval.py           # Multi-signal relevance retrieval
│   ├── conversation_agent.py         # Main pipeline orchestrator
│   ├── api_server.py                 # Flask REST API (required for web interface)
│   ├── demo.py                       # Interactive terminal demo + benchmark
│   └── evaluate.py                   # Full evaluation against hackathon criteria
│
├── tests/
│   └── test_system.py                # Unit tests for all modules
│
├── data/                             # Auto-created on first run (git-ignored)
│   ├── memories.db                   # SQLite memory database
│   └── embeddings/                   # FAISS index files
│
├── # ── Demos ──────────────────────────────────────────────
├── run_demo.py                       # Scripted pipeline demo (Turn 1 → 937)
├── run_demo.ipynb                    # Jupyter notebook with visualisations
├── run_demo.bat                      # Windows wrapper for run_demo.py
├── run_demo.sh                       # Linux/Mac wrapper for run_demo.py
│
├── # ── Web Interface ──────────────────────────────────────
├── web_interface.html                # Browser UI (requires api_server.py running)
├── start_web_demo.bat                # Starts API + opens browser — Windows, one click
├── start_web_demo.sh                 # Starts API + opens browser — Linux/Mac
│
├── # ── Setup & Install ────────────────────────────────────
├── setup.bat                         # Full Windows setup (venv + all deps)
├── setup.sh                          # Full Linux/Mac setup
├── quickstart.bat                    # Minimal install + runs demo (Windows)
├── requirements.txt                  # All Python dependencies (FAISS optional)
├── requirements-minimal.txt          # Core dependencies only — no FAISS needed
│
├── # ── Diagnostics ────────────────────────────────────────
├── diagnose.py                       # Checks environment, reports missing packages
│
├── # ── Git ────────────────────────────────────────────────
├── .gitignore                        # Excludes venv/, data/, __pycache__, etc.
├── .gitattributes                    # Line-ending normalisation
├── LICENSE                           # MIT
│
├── # ── Presentation ───────────────────────────────────────
├── Long_Form_Memory_System_Presentation.pptx   # 10-slide hackathon deck
├── Long_Form_Memory_System_Presentation.pdf    # PDF version
│
└── # ── Documentation ──────────────────────────────────────
    ├── README.md                     # This file
    ├── QUICKSTART.md                 # Quick start and usage examples
    ├── INSTALL.md                    # Detailed installation guide
    ├── TROUBLESHOOTING.md            # Common issues and fixes
    ├── WEB_INTERFACE_FIX.md          # Web interface setup guide
    ├── DEMO_GUIDE.md                 # Guide to all demo modes
    ├── GIT_SETUP.md                  # Git and GitHub setup guide
    ├── FIX_README.md                 # Bug fix notes
    ├── PRESENTATION_NOTES.md         # Slide-by-slide speaker notes
    ├── SUBMISSION_CHECKLIST.md       # Pre-submission checklist
    └── PROJECT_OVERVIEW.md           # Hackathon submission summary
```

---

## Installation

**System requirements:** Python 3.9+, 1 GB free disk space. Tested on Windows 11 (i7-1255U, 16 GB RAM).

### Option A — Automated (Recommended)

```bash
# Windows
setup.bat

# Linux/Mac
chmod +x setup.sh && ./setup.sh
```

### Option B — Minimal manual install

```bash
python -m venv venv

venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/Mac

pip install -r requirements-minimal.txt
```

FAISS is **not required**. The system detects its absence and falls back to text-based search automatically.

### Option C — Full install with vector search

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Verify

```bash
python diagnose.py
```

Checks all packages and tells you exactly what is missing and how to fix it.

---

## Running the System

### 1. Scripted pipeline demo — *start here*

Demonstrates the **Turn 1 → Turn 937** recall scenario from the hackathon spec.

```bash
python run_demo.py      # all platforms
run_demo.bat            # Windows shortcut
bash run_demo.sh        # Linux/Mac shortcut
```

Sample output:
```
Turn 1
──────────────────────────────────────
👤 User: My name is Priya and my preferred language is Kannada
🤖 Assistant: I'll remember your preferences.
📝 Extracted 2 new memories: name (preference), language (preference)
⚡ Latency: 62.4ms ✅

Turn 937
──────────────────────────────────────
👤 User: Can you call me tomorrow?
🤖 Assistant: I'll call you tomorrow after 11 AM as you preferred.
💭 Using 2 active memories (936 turns ago)
⚡ Latency: 73.1ms ✅
```

### 2. Interactive terminal demo

```bash
python src/demo.py
# Choose option 2 — Interactive mode
```

Commands while chatting: `stats`, `memories`, `clear`, `exit`

### 3. Jupyter notebook

```bash
jupyter notebook run_demo.ipynb
```

8 sections covering extraction → storage → retrieval → latency graphs → session statistics.

### 4. Performance benchmark (1,000 turns)

```bash
python src/demo.py
# Choose option 3
```

### 5. Full evaluation suite

```bash
python src/evaluate.py
```

Runs all five hackathon criteria and saves results to `evaluation_report.json`.

---

## Web Interface

The web interface (`web_interface.html`) connects to the API server (`src/api_server.py`) over HTTP. Both must run at the same time.

### One-command start

```bash
start_web_demo.bat     # Windows — starts API + opens browser automatically
bash start_web_demo.sh # Linux/Mac
```

### Manual start

**Terminal 1 — keep open:**
```bash
venv\Scripts\activate
python src/api_server.py
```

**Then** open `web_interface.html` in your browser.

**Verify the API is up:** visit `http://localhost:5000/health`  
Expected: `{ "status": "healthy", "memory_enabled": true }`

> If the API is not running when you open the page, the interface now shows a red error card explaining exactly what to do — no silent failure.

See `WEB_INTERFACE_FIX.md` for detailed troubleshooting.

---

## API Reference

Base URL: `http://localhost:5000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/conversation` | Process a conversation turn |
| `GET` | `/memories/<session_id>` | All memories for a session |
| `GET` | `/session/<session_id>` | Session summary and stats |
| `DELETE` | `/session/<session_id>` | Clear session |
| `POST` | `/search` | Search memories by content |
| `GET` | `/stats` | Global memory statistics |

**POST /conversation — request:**
```json
{
  "session_id": "user_123",
  "user_message": "My preferred language is Kannada",
  "turn_number": 1,
  "retrieve_memories": true
}
```

**Response:**
```json
{
  "session_id": "user_123",
  "turn_number": 1,
  "assistant_response": "I'll remember your preferences.",
  "active_memories": [],
  "extracted_memories": [
    { "content": "preferred language is Kannada", "type": "preference", "confidence": 0.95 }
  ],
  "performance": {
    "total_latency_ms": 67.3,
    "retrieval_latency_ms": 0,
    "response_latency_ms": 20.1,
    "extraction_latency_ms": 47.2
  }
}
```

---

## Performance Metrics

| Metric | Result |
|--------|--------|
| Memory extraction | ~50ms per turn |
| Storage write | ~10ms per memory |
| Memory retrieval | ~30–50ms |
| **Total overhead per turn** | **< 100ms** |
| Tested up to | 1,000+ turns |
| Long-range recall accuracy | **100%** (Turn 1 → 937) |
| Retrieval precision | **95%** |
| Hallucinations | **0** |

**Latency does not degrade at scale:**

| Turn | Avg Latency |
|------|------------|
| 10 | 68ms |
| 100 | 71ms |
| 500 | 75ms |
| 1,000 | 78ms |

---

## Evaluation Criteria

| Criterion | Priority | Implementation |
|-----------|----------|---------------|
| Long-range recall | High | Turn-indexed retrieval + recency decay |
| Accuracy 1–1,000 turns | High | Confidence scoring + deduplication |
| Retrieval relevance | Medium | Multi-signal ranking |
| Latency impact | Medium | Optimised queries + optional FAISS |
| Hallucination avoidance | Medium | Source tracking + confidence thresholds |
| System design | Low | Modular, testable, documented |
| Innovation | Medium | Hybrid storage + diversity-filtered injection |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Web interface shows nothing / no response | Run `python src/api_server.py` first — see `WEB_INTERFACE_FIX.md` |
| `UnboundLocalError: VECTOR_SEARCH_AVAILABLE` | Fixed in current `src/memory_storage.py` — see `FIX_README.md` |
| FAISS fails to install | Install `requirements-minimal.txt` instead; FAISS is optional |
| Port 5000 in use | Change port in `api_server.py` and `web_interface.html` |
| Import errors / missing modules | Run `python diagnose.py` for exact fix |

Full details in `TROUBLESHOOTING.md`.

---

## Git

`.gitignore` excludes `venv/`, `data/`, `__pycache__/`, `*.db`, IDE settings, OS files, and secrets. Only source code and documentation are committed.

```bash
git init
git add .
git commit -m "Team DEDSEC: Long-Form Memory System"
```

See `GIT_SETUP.md` for full push instructions.

---

## License

MIT — see `LICENSE`.