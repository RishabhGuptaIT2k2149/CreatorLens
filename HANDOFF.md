# CreatorLens — Claude Code Handoff

You are continuing work on a portfolio project. The previous session scaffolded the backend through Step 3. Your job is Steps 4–7. Read this document fully before running anything.

---

## 1. Project overview

**CreatorLens** is a YouTube Creator Intelligence Platform (SaaS-style portfolio project). Given a YouTube channel URL, it ingests every video, transcribes with Gemini, extracts brand/sponsor mentions, and exposes a RAG chat interface to answer questions about the channel.

The full product spec is in `CreatorLens_Blueprint.pdf` at the project root. Read it if you need deeper context. This handoff captures the MVP-scoped decisions.

**Owner:** Rishabh Gupta (soon-to-graduate software engineer). The goal is a portfolio-quality MVP that impresses recruiters — working end-to-end, clean structure, deployable. Not a production SaaS.

---

## 2. Scope — v0.1 trimmed MVP (locked)

The full blueprint is ~15 days of work. We explicitly trimmed it to ~5–7 days for v0.1. **Do not re-add the cut items unless the user asks.**

### In scope (v0.1)
- Paste YouTube channel URL → backend ingests up to 50 videos
- Gemini transcription (✅ done)
- Topic-aware chunking + local embeddings (AllMiniLM-L6-v2)
- ChromaDB local vector store
- Entity extraction (brand/product mentions) via Gemini
- Sponsorship detection via Gemini
- RAG chat endpoint
- React + Vite + Tailwind frontend with tabs (Overview, Brands, Sponsors, Chat)

### Cut for v0.1 (do NOT build these — add later if time allows)
- Supabase / Postgres → use **SQLite** locally
- Celery + Redis → use **FastAPI BackgroundTasks**
- PDF export (ReportLab)
- Audience interest clusters from comment analysis
- Deployment to Render/Vercel (local-only MVP first)
- Supabase Auth

---

## 3. Current status — what's built (Steps 1–3)

### ✅ Step 1 — Backend foundation
- Folder structure: `creatorlens/backend/` with venv
- `requirements.txt` pinned
- `config.py` loads env from `creatorlens/.env` using python-dotenv
- `main.py` with FastAPI app + CORS + `/` + `/health` routes
- `.env`, `.env.example`, `.gitignore` in place
- Git initialized

### ✅ Step 2 — YouTube API wrapper
- `services/youtube.py` — resolves channel URLs (@handle, /channel/UC…, /user/…) and lists video IDs from the uploads playlist
- `api/routes/channel.py` — `GET /channel/info` and `GET /channel/videos?url=…&limit=…`
- Tested against `https://www.youtube.com/@JerryRigEverything` (1,531 videos, 9.95M subs)

### ✅ Step 3 — Gemini transcription
- `services/transcriber.py` — calls Gemini 2.5 Flash with a YouTube `file_uri`, returns status/transcript/word_count/elapsed_sec. Saves transcript to `backend/transcripts/<video_id>.txt`
- `api/routes/debug.py` — `GET /debug/transcribe?video_id=…`
- Tested on 2 videos: `pIIC1MeLv6o` (1,766 words, 26s elapsed) and `3tyBy3e3ygc` (1,484 words). Quality verified — no timecodes, no `[music]` tags, sensible paragraphs, reads as natural spoken English.
- Model in `.env`: `GEMINI_MODEL=gemini-2.5-flash` (Gemini 2.0 Flash was deprecated — do not revert).

---

## 4. Tech stack (locked)

| Component | Choice | Notes |
|---|---|---|
| Backend | FastAPI | async, Swagger at `/docs` |
| Language | Python 3.11.2 | pinned — do not use 3.13 |
| Transcription | Gemini 2.5 Flash via `google-genai==1.33.0` | YouTube `file_uri` supported natively |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | 384-dim, local inference, zero cost |
| Vector DB | ChromaDB local (persist to `backend/chroma_db/`) | no Supabase in v0.1 |
| Metadata DB | **SQLite** via SQLAlchemy | file at `backend/creatorlens.db` |
| Entity extraction | Gemini 2.5 Flash w/ JSON schema prompt | see `Section 8` of blueprint for exact prompts |
| Job queue | FastAPI `BackgroundTasks` | no Celery/Redis in v0.1 |
| YouTube metadata | YouTube Data API v3 | 10k units/day free quota |
| Frontend | React + Vite + Tailwind + shadcn/ui | port 5173 |
| Charts | Recharts | |
| HTTP client (FE) | Axios | |

---

## 5. Critical gotchas (from blueprint §6)

1. **Gemini rate limit**: free tier is 15 req/min. Insert `time.sleep(RATE_LIMIT_DELAY_SEC)` (env var, default 4) between transcription calls. Already respected in Step 3 design.
2. **YouTube quota**: listing captions per video costs 50–200 units. **Do NOT** fetch captions via the YouTube API — send the video URL to Gemini instead.
3. **Chunking**: fixed-size (e.g., 512 tokens) destroys context. Chunk by paragraph with ~150–300 words, 20-word overlap. For our transcripts, paragraphs are already delineated by Gemini — split on `\n\n`.
4. **Embedding dimensionality lock-in**: AllMiniLM-L6-v2 = 384-dim. If the embedding model changes, every vector must be re-embedded. Do not change it mid-project.
5. **Transcription failures**: some videos return `NO_SPEECH` (music-heavy, non-English). Mark them as unprocessed and continue. Already handled in `services/transcriber.py`.
6. **Async in FastAPI**: ingestion is slow. `/analyse` returns a `job_id` immediately; the frontend polls `/status/{job_id}`. Use `BackgroundTasks`.
7. **CORS**: React on `localhost:5173` calling FastAPI on `localhost:8000` — already handled in `main.py` via `CORSMiddleware`.

---

## 6. Work remaining — Steps 4–7

### Step 4 — Ingestion pipeline (chunker + embedder + vector store)

Goal: a CLI script that ingests N videos from a channel end-to-end and lets you retrieve chunks by semantic query. No FastAPI wiring yet.

4.1 Install deps: `sentence-transformers`, `chromadb`, `sqlalchemy`, (maybe `numpy`).
4.2 Create `services/chunker.py`: paragraph-based chunking with 20-word overlap, 150–300 word targets. Return `list[{'chunk_text', 'video_id', 'chunk_index'}]`.
4.3 Create `services/embedder.py`: lazy-load AllMiniLM-L6-v2, expose `embed(texts: list[str]) -> list[list[float]]`.
4.4 Create `services/vector_store.py`: ChromaDB wrapper with one collection per channel (`collection_name=f"channel_{channel_id}"`). Methods: `upsert(chunks, embeddings, metadatas)`, `query(query_text, k=5) -> list[chunks]`.
4.5 Create `db/database.py` + `db/models.py`: SQLAlchemy with SQLite. Tables: `Channel(id, yt_channel_id, title, subscriber_count, video_count, uploads_playlist_id, ingested_at)`, `Video(id, video_id, channel_id, title, published_at, transcription_status, word_count)`, `IngestionJob(id, channel_id, status, progress, error, started_at, completed_at)`.
4.6 Create `workers/ingestion_worker.py`: orchestrator. Takes a channel URL. Resolves channel → lists up to MAX_VIDEOS_PER_CHANNEL → for each video: transcribe (respecting rate limit) → chunk → embed → upsert to ChromaDB → write metadata to SQLite. Updates IngestionJob progress.
4.7 Create `scripts/ingest_cli.py`: calls the worker with `@JerryRigEverything`, prints progress, prints a test retrieval on "phone durability test".
4.8 **Validation**: run the CLI against JerryRigEverything with `MAX_VIDEOS_PER_CHANNEL=3` (override via env for fast testing). Verify 3 transcripts ingested, ChromaDB has ~15–30 chunks, retrieval returns relevant ones.

### Step 5 — Wire ingestion to FastAPI
5.1 `POST /analyse` → body: `{channel_url}`, returns `{job_id}`. Uses `BackgroundTasks` to kick off ingestion.
5.2 `GET /channel/{id}/status` → `{status, progress, videos_done, videos_total}`.
5.3 `GET /channel/{id}/overview` → channel stats, top theme keywords, upload frequency.
5.4 Move `MAX_VIDEOS_PER_CHANNEL` cap to a safety check, not a hard ingest stop.

### Step 6 — RAG + entity extraction + sponsorship detection
6.1 `services/extractor.py` — Gemini prompt from blueprint §8 (Entity Extraction Prompt). Structured JSON output. Run over each chunk during ingestion; store in SQLite `BrandMention(id, video_id, chunk_id, name, category, mention_type, sentiment, context)`.
6.2 `services/sponsorship.py` — heuristic first (keyword list: "sponsored by", "thanks to our sponsor", "check out [brand] using code"), LLM fallback with blueprint §8 Sponsorship Detection Prompt. Store `SponsorshipSegment(id, video_id, sponsor_name, confidence, evidence, timestamp_approx)`.
6.3 `api/routes/channel.py` (extend): `GET /channel/{id}/brands` (grouped by category + sentiment), `GET /channel/{id}/sponsors` (timeline).
6.4 `api/routes/chat.py` → `POST /channel/{id}/chat` with `{question, history}`. Embed question → query ChromaDB top-k=5 → pass chunks to Gemini with blueprint §8 RAG Chat Prompt → stream response.

### Step 7 — React frontend (Vite + Tailwind + shadcn/ui)
7.1 Scaffold with `npm create vite@latest frontend -- --template react`. Add Tailwind, shadcn/ui, axios, recharts, react-router-dom.
7.2 `src/api/client.js` — axios instance pointed at `http://localhost:8000`.
7.3 `Home.jsx` — SearchBar for channel URL → POST /analyse → navigate to `/channel/:id` with job_id in state.
7.4 `Channel.jsx` — tabs: Overview / Brands / Sponsors / Chat. Poll `/status` until done, then load tab data.
7.5 Components: `SearchBar`, `OverviewCard`, `BrandsTable`, `SponsorsTimeline`, `ChatPanel` (streaming).
7.6 Loading states, empty states, error boundaries — must not be skipped for demo polish.

---

## 7. How the user wants you to work

These are non-negotiable. The user (Rishabh) stated them explicitly in the previous session:

1. **Always specify EXACTLY where** to run each command: project root (`creatorlens/`) / `backend/` / `frontend/` / or "inside venv".
2. **Always mention if the venv must be activated** before running a command. Prompt prefix should show `(venv)`.
3. **Give commands in exact order. No skipping steps.**
4. **Keep tasks small and incremental.** Do not build multiple components in one go without a test checkpoint.
5. **After giving code, always show how to test it and what the expected output looks like.**
6. **If something depends on API keys or env vars, explicitly say where to put them** (`.env`, `config.py`, etc.).
7. **Don't over-explain concepts** unless asked. Focus on execution clarity. Rishabh is comfortable with the terminal but new to most of these technologies.
8. **Production-clean structure matters** — this is a portfolio project.
9. **Prefer editing existing files over creating redundant new ones.** Follow the folder structure already on disk.

---

## 8. Key file paths

```
~/Desktop/creatorlens/
├── .env                        # secrets — already populated
├── .env.example
├── .gitignore
├── CreatorLens_Blueprint.pdf   # product spec — reference as needed
├── HANDOFF.md                  # this file
├── backend/
│   ├── venv/                   # Python 3.11.2 venv — ACTIVATE before any Python/pip command
│   ├── requirements.txt
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Settings loader
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── channel.py      # /channel/info, /channel/videos
│   │       └── debug.py        # /debug/transcribe
│   ├── services/
│   │   ├── __init__.py
│   │   ├── youtube.py
│   │   └── transcriber.py
│   └── transcripts/            # transcribed .txt files (3 already here)
└── frontend/                   # empty — scaffold in Step 7
```

---

## 9. Environment variables (already in `.env`)

```
YOUTUBE_API_KEY=<loaded>
GEMINI_API_KEY=<loaded>
GEMINI_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHROMA_PERSIST_DIR=./chroma_db
MAX_VIDEOS_PER_CHANNEL=50
RATE_LIMIT_DELAY_SEC=4
CORS_ORIGINS=http://localhost:5173
TEST_CHANNEL_URL=https://www.youtube.com/@JerryRigEverything
```

**Note:** API keys were exposed in a chat log during the previous session. User should rotate them before public deployment. Not urgent for local development.

---

## 10. Starting instructions for Claude Code

Your first message to the user should be short:

> I've read HANDOFF.md and the project structure. Starting Step 4 — the ingestion pipeline. I'll do 4.1 (install sentence-transformers + chromadb + sqlalchemy into the venv) and 4.2 (build the chunker) first, test the chunker on the existing transcripts, and report back before moving to the embedder.

Then execute. Keep the user's 9 working-preferences from §7 in mind on every command. When you hit the first major checkpoint (Step 4.8 — CLI ingestion of 3 videos works end-to-end with a sensible retrieval result), pause and confirm with the user before moving to Step 5.

Good luck. Ship it.
