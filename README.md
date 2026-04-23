# CreatorLens
 
> YouTube creator intelligence platform. Convert any channel into a searchable knowledge base, extract brand mentions, detect sponsorships, and ask grounded questions about the content.
 
Built for media houses and advertising agencies who spend hundreds of hours researching influencers before every brand deal. CreatorLens automates that entire process.
 
**Live Demo:** [Coming soon]
**Author:** [Rishabh Gupta](https://linkedin.com/in/your-handle) · Indore, India
 
---
 
## What It Does
 
Paste a YouTube channel URL. CreatorLens will:
 
1. Pull every video from the channel
2. Transcribe them using Gemini
3. Extract every brand mentioned across the creator's catalogue
4. Tag the sentiment behind each mention (positive, neutral, negative)
5. Detect which segments are sponsored ad-reads
6. Let you ask anything about the channel through a RAG-powered chat, with citations
All grounded in the creator's actual content. Nothing pulled from the open internet. Everything traceable back to the exact video and timestamp.
 
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
 
| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI (Python) | Async, auto-docs, built for AI APIs |
| Transcription | Gemini 2.0 Flash | Accepts video URLs directly, no audio extraction needed |
| Embeddings | AllMiniLM-L6-v2 | Runs locally, zero API cost |
| Vector DB | ChromaDB (dev) / Supabase pgvector (prod) | Local dev, easy prod migration |
| Entity Extraction | Gemini Flash + structured output | Reliable JSON extraction for brand data |
| Database | PostgreSQL (Supabase) | Stores channel metadata and extracted entities |
| Frontend | React + Vite + Tailwind | Fast dev server, small bundles |
| Data API | YouTube Data API v3 | Channel and video metadata |
 
Total monthly infrastructure cost at demo scale: **zero rupees**. Fully built on free tiers.
 
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
│ YouTube │      │    Gemini    │    │  AllMiniLM   │
│   API   │─────▶│ Transcription│───▶│   Embedder   │
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
                 │  PostgreSQL  │           │
                 │  (entities)  │           │
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
 
## The RAG Flow
 
When a user asks a question in the chat:
 
1. Question is embedded using AllMiniLM
2. Top 5 similar chunks are pulled from ChromaDB
3. Retrieved chunks + question are sent to Gemini with a grounding prompt
4. Answer streams back with citations to the exact video chunks
Example query: *"Does Arun talk about smartwatches?"*
 
The system returns: *"Yes, he does. Arun recently reviewed the Garmin Venu 4..."* with chunk references at the bottom of the response.
 
---
 
## Key Engineering Decisions
 
**Why Gemini for transcription instead of Whisper**
Gemini accepts YouTube video URLs directly. Whisper requires downloading the audio first, which adds another failure point and more infrastructure. One less thing to maintain.
 
**Why local embeddings instead of OpenAI**
AllMiniLM-L6-v2 gives 384-dimensional vectors with quality that's more than sufficient for transcript retrieval. Running locally means zero per-request cost at scale.
 
**Why chunking by paragraph, not fixed tokens**
Fixed-size chunks break mid-sentence and destroy context. Paragraph-based chunking with a 20-word overlap preserves semantic continuity. This single decision made retrieval quality jump noticeably.
 
**Why background jobs for ingestion**
Ingesting a 200-video channel takes 10-15 minutes. Running this synchronously in a request handler would time out every user. The `/analyse` endpoint returns a `job_id` immediately and the frontend polls for completion.
 
---
 
## Getting Started
 
### Prerequisites
- Python 3.11+
- Node.js 20+
- A Google Cloud project with YouTube Data API v3 enabled
- A Google AI Studio API key for Gemini
### Backend Setup
 
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
uvicorn main:app --reload
```
 
Backend runs on `http://localhost:8000`. Swagger docs at `/docs`.
 
### Frontend Setup
 
```bash
cd frontend
npm install
npm run dev
```
 
Frontend runs on `http://localhost:5173`.
 
### Environment Variables
 
```
YOUTUBE_API_KEY=your_youtube_api_key
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql://user:pass@localhost:5432/creatorlens
CHROMA_PERSIST_DIR=./chroma_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
GEMINI_MODEL=gemini-2.0-flash
MAX_VIDEOS_PER_CHANNEL=50
RATE_LIMIT_DELAY_SEC=4
CORS_ORIGINS=http://localhost:5173
```
 
---
 
## Limitations & Known Issues
 
- Gemini free tier allows 15 requests per minute. A 200-video channel hits this hard. The system handles it with a rate-limited queue but ingestion is slower as a result.
- Videos without captions and with non-English audio occasionally return poor transcripts. These are flagged as `unprocessed` and skipped.
- Sentiment classification is LLM-based and can drift on sarcasm or nuanced reviews. Human review still recommended for high-stakes deals.
- No auth yet. MVP is single-tenant.
---
 
## Roadmap
 
- [ ] Multi-tenant auth via Supabase
- [ ] Bulk channel comparison (compare 5 creators side by side)
- [ ] Audience interest clustering from comment analysis
- [ ] Export-to-PDF brand fit reports
- [ ] Webhook integrations for agency CRMs
---
 
## Monetisation Plan
 
Built to be a SaaS eventually. Planned tiers:
 
- **Free** — 3 channel analyses/month, basic brand detection
- **Pro (₹999/mo)** — 25 analyses/month, full sentiment + sponsors + chat
- **Agency (₹4999/mo)** — unlimited, team workspace, API access
Currently focused on showcasing the build. Reach out if you want access.
 
---
 
## About
 
Built by Rishabh Gupta over two weeks in April 2026 as part of a final-year portfolio push.
 
**Looking for:** Backend / AI engineering roles. Final year IT, graduating 2026.
**Contact:** rishabh.gupta7692@gmail.com · [LinkedIn](https://linkedin.com/in/your-handle)
 
If you're an agency that would actually use this, my DMs are open.
 
---
 
## License
 
MIT — do whatever you want with it, just don't blame me if it breaks.
 
