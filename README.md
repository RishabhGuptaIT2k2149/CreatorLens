# CreatorLens

> YouTube creator intelligence platform. Convert any channel into a searchable knowledge base, extract brand mentions, detect sponsorships, and ask grounded questions about the content.

Built for media houses and advertising agencies who spend hundreds of hours researching influencers before every brand deal. CreatorLens automates that entire process.

**Author:** [Rishabh Gupta](https://www.linkedin.com/in/rishabh-gupta-150082277/) · Indore, India

---

## What It Does

Paste a YouTube channel URL. CreatorLens will:

1. Pull every video from the channel (up to 50 by default)
2. Transcribe them using Gemini — no audio download required
3. Extract every brand mentioned across the creator's catalogue
4. Tag the sentiment behind each mention (positive, neutral, negative)
5. Detect which segments are sponsored ad-reads
6. Let you ask anything about the channel through a RAG-powered chat, with citations

All grounded in the creator's actual content. Nothing pulled from the open internet. Everything traceable back to the exact video.

---

## Why It Exists

Before a brand signs a deal with a YouTuber, an agency team has to:

- Watch hundreds of videos to understand the creator's voice
- Manually note which brands they've already plugged
- Guess whether their audience overlaps with the brand's target
- Figure out what gaps exist in their current sponsorship roster

This takes days. Sometimes weeks. For a single influencer.

CreatorLens does it in minutes.

---

## Tech Stack

### Backend

| Component | Technology | Version |
|---|---|---|
| Framework | FastAPI | 0.115.4 |
| Language | Python | 3.11.2 |
| ASGI Server | Uvicorn | 0.32.0 |
| Validation | Pydantic | 2.9.2 |
| YouTube metadata | YouTube Data API v3 via `google-api-python-client` | 2.149.0 |
| Transcription & LLM | Gemini 2.0 Flash via `google-genai` | 1.33.0 |
| Embeddings | Google `text-embedding-004` (REST API) | — |
| Vector store | ChromaDB (local, persisted to disk) | 1.5.8 |
| Metadata database | SQLite via SQLAlchemy | 2.0.49 |
| Job queue | FastAPI `BackgroundTasks` | — |
| Config | python-dotenv | 1.0.1 |


note: before it used ALLMiniLm v6, but due to issues with deployment we switched to google embedder
### Frontend

| Component | Technology | Version |
|---|---|---|
| Framework | React | 19.2.5 |
| Build tool | Vite | 8.0.9 |
| Styling | Tailwind CSS | 4.2.4 |
| Routing | react-router-dom | 7.14.2 |
| Charts | Recharts | 3.8.1 |
| Icons | lucide-react | 1.8.0 |
| HTTP client | Axios | 1.15.2 |
| Linting | ESLint | 9.39.4 |

Total monthly infrastructure cost at demo scale: **zero**. Fully built on free tiers.

---

## Architecture

```
                 ┌──────────────┐
                 │  User pastes │
                 │  channel URL │
                 └──────┬───────┘
                        │
                        ▼
           ┌────────────────────────┐
           │   FastAPI /analyse     │
           │   returns job_id       │
           └────────────┬───────────┘
                        │
                        ▼
           ┌────────────────────────┐
           │  Background Ingestion  │
           │       Pipeline         │
           └────────────┬───────────┘
                        │
     ┌──────────────────┼──────────────────┐
     ▼                  ▼                  ▼
┌─────────┐      ┌──────────────┐    ┌──────────────┐
│ YouTube │      │    Gemini    │    │   Google     │
│   API   │─────▶│ Transcription│───▶│ text-embed   │
└─────────┘      └──────┬───────┘    └──────┬───────┘
                        │                   │
                        ▼                   ▼
                 ┌──────────────┐    ┌──────────────┐
                 │    Gemini    │    │   ChromaDB   │
                 │   Extractor  │    │  Vector Store│
                 └──────┬───────┘    └──────┬───────┘
                        │                   │
                        ▼                   │
                 ┌──────────────┐           │
                 │   SQLite DB  │           │
                 │  (entities + │           │
                 │   metadata)  │           │
                 └──────────────┘           │
                                            │
                  ┌─────────────────────────┘
                  │
                  ▼
           ┌──────────────┐
           │  React UI    │
           │  4 tabs:     │
           │  - Overview  │
           │  - Brands    │
           │  - Sponsors  │
           │  - RAG Chat  │
           └──────────────┘
```

---

## Data Models

**SQLite tables (via SQLAlchemy):**

- `channels` — channel metadata (title, subscriber count, uploads playlist ID, ingested_at)
- `videos` — per-video status (transcription_status: pending/ok/no_speech/error, word count)
- `ingestion_jobs` — job tracking (status, progress, total, error, timestamps)
- `brand_mentions` — extracted brands per video (name, category, mention_type, sentiment, context)
- `sponsorship_segments` — detected ad-reads (sponsor_name, confidence, evidence)

---

## The RAG Flow

When a user asks a question in the chat:

1. Question is embedded using Google `text-embedding-004`
2. Top 5 similar chunks are pulled from ChromaDB (cosine similarity)
3. Retrieved chunks + question are sent to Gemini with a grounding prompt
4. Answer streams back with citations to the exact video chunks

Example query: *"Does this creator talk about smartwatches?"*

The system returns a grounded answer referencing the specific videos where the topic appeared.

---

## Key Engineering Decisions

**Why Gemini for transcription instead of Whisper**
Gemini accepts YouTube video URLs directly via `file_uri`. Whisper requires downloading the audio first — another failure point and more infrastructure. One less thing to maintain.

**Why Google `text-embedding-004` instead of local sentence-transformers**
The original plan used AllMiniLM-L6-v2 locally, but switched to Google's embedding API for consistency with the rest of the Gemini stack. Zero infra to set up, and the quality is excellent for retrieval.

**Why chunking by paragraph, not fixed tokens**
Fixed-size chunks break mid-sentence and destroy context. Gemini's transcripts naturally use `\n\n` paragraph breaks. Splitting on these with a 20-word overlap preserves semantic continuity. This single decision made retrieval quality jump noticeably.

**Why SQLite instead of PostgreSQL**
This is an MVP. SQLite removes the need to spin up a database server locally. SQLAlchemy abstracts the dialect, so migrating to Postgres later is a one-line change in `DATABASE_URL`.

**Why background jobs for ingestion**
Ingesting a 50-video channel takes 3–10 minutes due to Gemini rate limits (15 req/min on free tier). Running this synchronously would time out every request. `POST /analyse` returns a `job_id` immediately; the frontend polls `GET /channel/{id}/status` until done.

---

## Getting Started

### Prerequisites

- Python 3.11.x
- Node.js 20+
- A Google Cloud project with **YouTube Data API v3** enabled
- A **Google AI Studio** API key (for Gemini + text-embedding-004)

### Backend Setup

```bash
# Run from project root: creatorlens/
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy and fill in API keys
cp ../.env.example ../.env
# Edit .env and set YOUTUBE_API_KEY and GEMINI_API_KEY

uvicorn main:app --reload
```

Backend runs on `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

### Frontend Setup

```bash
# Run from project root: creatorlens/
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`.

### Environment Variables

Create a `.env` file at the project root (`creatorlens/.env`):

```env
YOUTUBE_API_KEY=your_youtube_data_api_v3_key
GEMINI_API_KEY=your_google_ai_studio_key

# Models
GEMINI_MODEL=gemini-2.0-flash
EMBEDDING_MODEL=text-embedding-004

# Storage (paths are relative to backend/)
CHROMA_PERSIST_DIR=./chroma_db

# Limits
MAX_VIDEOS_PER_CHANNEL=50
RATE_LIMIT_DELAY_SEC=4

# Dev
CORS_ORIGINS=http://localhost:5173
TEST_CHANNEL_URL=https://www.youtube.com/@YourTestChannel
```

---

## Project Structure

```
creatorlens/
├── .env                          # secrets — never commit this
├── .env.example
├── backend/
│   ├── main.py                   # FastAPI app + CORS + routes
│   ├── config.py                 # Settings loaded from .env
│   ├── requirements.txt
│   ├── api/routes/
│   │   ├── channel.py            # GET /channel/info, /channel/videos
│   │   │                         # GET /channel/{id}/overview, /brands, /sponsors
│   │   ├── analyse.py            # POST /analyse, GET /channel/{id}/status
│   │   ├── chat.py               # POST /channel/{id}/chat
│   │   └── debug.py              # GET /debug/transcribe (dev only)
│   ├── services/
│   │   ├── youtube.py            # YouTube Data API v3 wrapper
│   │   ├── transcriber.py        # Gemini transcription via file_uri
│   │   ├── chunker.py            # Paragraph-based chunking
│   │   ├── embedder.py           # Google text-embedding-004 REST calls
│   │   ├── vector_store.py       # ChromaDB wrapper (one collection per channel)
│   │   ├── extractor.py          # Brand/entity extraction via Gemini
│   │   └── sponsorship.py        # Sponsorship detection (heuristic + LLM)
│   ├── db/
│   │   ├── database.py           # SQLAlchemy engine + session + migrations
│   │   └── models.py             # Channel, Video, IngestionJob, BrandMention, SponsorshipSegment
│   ├── workers/
│   │   └── ingestion_worker.py   # End-to-end pipeline orchestrator
│   ├── scripts/
│   │   └── ingest_cli.py         # CLI entrypoint for manual ingestion
│   └── transcripts/              # Cached .txt transcripts per video_id
└── frontend/
    ├── src/
    │   ├── App.jsx               # Router — Home + Channel pages
    │   ├── pages/
    │   │   ├── Home.jsx          # URL input → POST /analyse
    │   │   └── Channel.jsx       # 4-tab dashboard with polling
    │   └── components/           # SearchBar, OverviewCard, BrandsTable, etc.
    ├── package.json
    └── vite.config.js
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health + config check |
| `GET` | `/channel/info?url=` | Resolve channel metadata |
| `GET` | `/channel/videos?url=&limit=` | List video IDs from channel |
| `POST` | `/analyse` | Start ingestion job, returns `job_id` |
| `GET` | `/channel/{id}/status` | Poll ingestion progress |
| `GET` | `/channel/{id}/overview` | Channel stats + themes |
| `GET` | `/channel/{id}/brands` | Brand mentions grouped by category |
| `GET` | `/channel/{id}/sponsors` | Detected sponsorship segments |
| `POST` | `/channel/{id}/chat` | RAG chat with `{question, history}` |

Full interactive docs at `http://localhost:8000/docs` when the backend is running.

---

## Limitations & Known Issues

- Gemini free tier caps at 15 requests/minute. A 50-video channel takes ~5 minutes to ingest. The system handles this with a rate-limited queue.
- Videos without intelligible speech (music-only, non-English audio) are flagged as `no_speech` and skipped.
- Sentiment classification is LLM-based and can drift on sarcasm or nuanced reviews. Human review recommended for high-stakes decisions.
- No auth. MVP is single-tenant, local-only.

---

## Roadmap

- [ ] Deploy to Render (backend) + Vercel (frontend)
- [ ] Multi-tenant auth via Supabase
- [ ] Bulk channel comparison (compare creators side by side)
- [ ] Audience interest clustering from comment analysis
- [ ] Export-to-PDF brand fit reports
- [ ] Postgres migration for production

---

## About

Built by Rishabh Gupta in April 2026 as part of a final-year portfolio push.

**Looking for:** Backend / AI engineering roles. Final year IT, graduating 2026.
**Contact:** rishabh.gupta7692@gmail.com · [LinkedIn](https://linkedin.com/in/your-handle)

---

## License

MIT — do whatever you want with it, just don't blame me if it breaks.