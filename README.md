# Python Programming Q&A Assistant

An AI-powered question-answering system for Python learners, built on a **RAG (Retrieval-Augmented Generation)** pipeline grounded in Stack Overflow data. Answers are generated strictly from retrieved context — no hallucinations.

> **Assessment:** Analytics Vidhya — AI Engineer Round 1

---

## Architecture

```
User Question
      │
      ▼
┌─────────────────────────────────────────┐
│           Next.js 14 UI  (:3000)        │
└────────────────────┬────────────────────┘
                     │  HTTP POST /ask
                     ▼
┌─────────────────────────────────────────┐
│           FastAPI  (:8000)              │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│           RAG Pipeline                  │
│                                         │
│  1. Embed question                      │
│     sentence-transformers               │
│     all-MiniLM-L6-v2 (384-dim, CPU)    │
│              │                          │
│  2. Retrieve — FAISS cosine search      │
│     Top-5 Stack Overflow Q&A pairs      │
│              │                          │
│  3. Augment — inject context            │
│     "Answer ONLY from context"          │
│     temperature = 0.1                   │
│              │                          │
│  4. Generate — google-genai SDK         │
│     gemini-2.5-flash                    │
│              │                          │
│  5. Return answer + sources + latency   │
└─────────────────────────────────────────┘
                     │
                     ▼
              JSON Response
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI + Uvicorn (async) |
| **Validation** | Pydantic v2 |
| **RAG Retrieval** | LangChain + FAISS (in-process) |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` (384-dim, CPU) |
| **Vector Store** | FAISS (no server needed; swap to Pinecone at scale) |
| **LLM** | Google Gemini 2.5 Flash via **`google-genai` SDK** (free tier) |
| **Frontend** | Next.js 14 + TypeScript + Tailwind CSS |
| **Dataset** | Stack Overflow Python Q&A (Kaggle, score ≥ 5) |

> **Note:** LangChain is used **only** for retrieval orchestration (FAISS wrapper).  
> The LLM call goes directly through the `google-genai` SDK — no LangChain LLM wrapper.

---

## Quick Start

### 1. Clone & install

```bash
git clone <repo-url>
cd "Python Programming Q&A Assistant"
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — add your Google AI Studio key
# GOOGLE_API_KEY=your_key_here
```

Get a free API key at → https://aistudio.google.com/apikey

### 3. Run backend (uses bundled 50 Q&A pairs automatically)

```bash
uvicorn app.main:app --reload
# API available at http://localhost:8000
# Swagger UI at http://localhost:8000/docs
```

### 4. Run frontend (optional)

```bash
cd frontend
npm install
npm run dev
# UI available at http://localhost:3000
```

---

## Building the Full Index (Optional)

The app ships with **50 curated Python Q&A pairs** as fallback. For the full Stack Overflow dataset:

```bash
# 1. Place your Kaggle API credentials at ~/.kaggle/kaggle.json
# 2. Process the dataset (downloads + cleans HTML + filters score ≥ 5)
python -m data.process --download

# 3. Build the FAISS index
python scripts/build_index.py
```

This creates `data/faiss_index/` which the app loads automatically on startup.

---

## API Reference

### `GET /health`

Returns service status — use as a liveness probe.

```json
{
  "status": "healthy",
  "vector_store_loaded": true,
  "total_documents": 50,
  "model": "gemini-2.5-flash",
  "version": "1.0.0"
}
```

### `POST /ask`

Ask a Python programming question.

**Request:**
```json
{
  "question": "How do I reverse a list in Python?",
  "top_k": 5
}
```

| Field | Type | Rules |
|-------|------|-------|
| `question` | string | 5–1000 characters, required |
| `top_k` | integer | 1–20, optional (default: 5) |

**Response:**
```json
{
  "question": "How do I reverse a list in Python?",
  "answer": "You can reverse a list using `[::-1]` slice or `.reverse()`...",
  "sources": [
    {
      "title": "How do I reverse a list in Python?",
      "score": 150,
      "snippet": "Q: How do I reverse..."
    }
  ],
  "model": "gemini-2.5-flash",
  "latency_ms": 3409.2,
  "timestamp": "2026-06-14T10:00:00"
}
```

**Error codes:**

| Code | Meaning |
|------|---------|
| `400` | Bad request (empty or invalid question) |
| `422` | Pydantic validation failure (auto-generated) |
| `503` | RAG pipeline still loading |
| `500` | Internal server error |

### cURL Example

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is a list comprehension in Python?"}'
```

---

## Running Tests

```bash
# Unit tests — fully mocked, no API key required
pytest tests/test_api.py -v

# Integration tests — hits real Gemini API (needs GOOGLE_API_KEY in .env)
pytest tests/test_queries.py -v -s -m integration

# Generate test_results.json for submission
python tests/test_queries.py
```

**Test results (10/10 pass):** → `data/test_results.json`

---

## RAG Design — Why Strict Grounding?

The prompt explicitly forbids outside knowledge:

```
Answer ONLY using information from the context — do NOT use outside knowledge.
If the context does not contain enough information, say exactly:
"I don't have enough data in my knowledge base..."
```

Combined with `temperature=0.1`, this eliminates hallucination and ensures every answer is traceable back to a real Stack Overflow post.

---

## Deployment

### Hugging Face Spaces (Recommended — free)

1. Create a Space with **Docker** SDK
2. Push this repo
3. Add `GOOGLE_API_KEY` as a Space Secret
4. The `Dockerfile` exposes port `7860` (HF default)

### Render / Railway

```bash
# Start command
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Add `GOOGLE_API_KEY` as an environment variable in the dashboard.

---

## Scaling to 100+ Concurrent Users

| Concern | Current | At Scale |
|---------|---------|----------|
| **Latency** | ~3.3s avg | Streaming SSE + multiple Uvicorn workers behind Nginx |
| **Vector Search** | In-process FAISS | Pinecone / Qdrant — distributed, sub-10ms |
| **LLM Calls** | Synchronous | Async batch + Gemini prompt caching (up to 75% cost reduction) |
| **Caching** | None | Redis semantic cache — ~40% hit rate → $18/day vs $30/day |
| **Observability** | stdout logging | LangSmith LLM traces + Datadog APM + structured JSON logs |

---

## Project Structure

```
.
├── app/
│   ├── main.py              # FastAPI app, lifespan, CORS, error handlers
│   ├── rag.py               # RAG pipeline — FAISS retrieval + Gemini generation
│   ├── models.py            # Pydantic v2 request/response models
│   └── config.py            # Settings via pydantic-settings (.env)
├── data/
│   ├── process.py           # Kaggle dataset downloader & HTML cleaner
│   ├── sample_data.json     # 50 curated Python Q&A pairs (bundled fallback)
│   └── test_results.json    # Integration test results (10/10 pass)
├── frontend/
│   ├── app/page.tsx         # Main chat UI page
│   ├── components/
│   │   ├── MarkdownAnswer.tsx   # Syntax-highlighted markdown renderer
│   │   ├── SourceCard.tsx       # Collapsible SO source cards
│   │   └── LoadingDots.tsx      # Animated loading indicator
│   └── types/api.ts         # TypeScript types for API responses
├── scripts/
│   └── build_index.py       # Builds FAISS index from processed dataset
├── tests/
│   ├── test_api.py          # 14 unit tests (mocked — fast)
│   └── test_queries.py      # 10 integration tests + JSON result exporter
├── Dockerfile               # Ready for HF Spaces / Render / Railway
├── requirements.txt
├── pytest.ini
└── .env.example
```

---

## Key Design Decisions

1. **`google-genai` SDK directly** — no LangChain LLM wrapper; fewer abstractions, easier debugging
2. **sentence-transformers on CPU** — no GPU required, runs free on any machine
3. **FAISS in-process** — zero infra overhead for the demo; swap to Pinecone for production
4. **Temperature 0.1 + strict prompt** — deterministic, hallucination-free answers grounded in SO data
5. **Pydantic v2 validation** — contract-first API with clean 422 errors on bad input
