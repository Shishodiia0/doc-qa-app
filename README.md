# Doc Q&A — AI-Powered Document & Multimedia Q&A

A full-stack web application to upload PDFs, audio, and video files and chat with an AI about their content. Supports real-time streaming responses, semantic vector search, timestamp-linked playback, and multi-user JWT authentication.

---

## Architecture

```
frontend (React + Vite + Tailwind)  →  nginx  →  backend (FastAPI + Python)
                                                       ├── MongoDB   (documents & users)
                                                       ├── Redis     (vector cache + response cache)
                                                       ├── Groq API  (LLaMA 3.1 chat + Whisper transcription)
                                                       └── FAISS     (local vector search)
```

---

## Features

| Feature | Detail |
|---|---|
| File upload | PDF, MP3/WAV/M4A, MP4/MOV/AVI/MKV (up to 100MB) |
| PDF extraction | pdfplumber — extracts text from all pages |
| Audio/Video transcription | Groq Whisper with segment timestamps |
| Auto summarisation | LLaMA 3.1 summary generated on upload |
| Semantic search | FAISS + TF-IDF hashing (no GPU, no external API) |
| Streaming chat | Server-Sent Events (SSE) real-time responses |
| Timestamp playback | "Play at X:XX" button jumps media to answer |
| Clickable transcript | Click any transcript segment to jump to that time |
| Multi-user auth | JWT register/login |
| Rate limiting | slowapi per-IP |
| Caching | Redis (vector index + chat response cache) |
| Test coverage | 96%+ (65 backend tests, 40+ frontend tests) |
| CI/CD | GitHub Actions (test + Docker Hub push) |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, Uvicorn |
| LLM | Groq API — `llama-3.1-8b-instant` (free tier) |
| Transcription | Groq Whisper — `whisper-large-v3-turbo` (free tier) |
| Vector Search | FAISS (local, CPU-only) |
| Database | MongoDB 7 (Motor async driver) |
| Cache | Redis 7 |
| Frontend | React 18, TypeScript, Tailwind CSS, Vite |
| State | Zustand |
| Containers | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## Quick Start (Docker Compose)

### Prerequisites
- Docker ≥ 24 and Docker Compose v2
- A free Groq API key from **https://console.groq.com**

### 1. Clone & configure

```bash
git clone https://github.com/Shishodiia0/doc-qa-app.git
cd doc-qa-app
cp backend/.env.example backend/.env
# Edit backend/.env and set GROQ_API_KEY=gsk_...
```

### 2. Start all services

```bash
docker compose up --build
```

Open **http://localhost** in your browser.

### 3. Use the app

1. Click **Register** → create a username & password
2. Click **Login**
3. Drag & drop a PDF, audio, or video file
4. Wait for the green checkmark (10–30 seconds)
5. Click the document → ask questions in the chat
6. For audio/video — click **"Play at X:XX"** to jump to the relevant moment

---

## Local Development (Virtual Environment)

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # set GROQ_API_KEY
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

> The Vite dev server proxies `/api` → `http://localhost:8000`.

### Infrastructure (local)

```bash
docker run -d -p 27017:27017 --name mongo mongo:7
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

---

## API Reference

All endpoints are prefixed `/api/v1`. Protected routes require `Authorization: Bearer <token>`.

### Auth

| Method | Path | Body | Description |
|---|---|---|---|
| POST | `/auth/register` | `{username, password}` | Create account |
| POST | `/auth/login` | `{username, password}` | Returns JWT |

### Documents

| Method | Path | Description |
|---|---|---|
| POST | `/documents/upload` | Upload file (multipart/form-data) |
| GET | `/documents/` | List user's documents |
| GET | `/documents/{id}` | Get document + summary + segments |
| DELETE | `/documents/{id}` | Delete document |
| GET | `/documents/{id}/stream` | Stream media file for playback |

### Chat

| Method | Path | Body | Description |
|---|---|---|---|
| POST | `/chat/` | `{document_id, message, history}` | Single response with caching |
| POST | `/chat/stream` | `{document_id, message, history}` | SSE streaming response |

**Chat response:**
```json
{
  "answer": "The assignment requires...",
  "timestamp": 42.5,
  "segment_end": 48.0
}
```
`timestamp` / `segment_end` are `null` for PDFs and when no matching segment is found.

**SSE stream events:**
```
data: {"token": "The "}
data: {"token": "answer"}
data: {"done": true, "timestamp": 42.5}
```

---

## Testing

### Backend (96%+ coverage)

```bash
cd backend
source .venv/bin/activate
GROQ_API_KEY=test-key SECRET_KEY=test-secret pytest
```

Coverage report printed to terminal and written to `coverage.xml`.

### Frontend

```bash
cd frontend
npm test
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | — | **Required** — get free at https://console.groq.com |
| `MONGODB_URL` | `mongodb://mongo:27017` | MongoDB connection string |
| `MONGODB_DB` | `docqa` | Database name |
| `REDIS_URL` | `redis://redis:6379` | Redis connection string |
| `SECRET_KEY` | `change-me` | JWT signing secret (use a long random string) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token TTL in minutes |
| `MAX_FILE_SIZE_MB` | `100` | Max upload file size |
| `UPLOAD_DIR` | `/tmp/uploads` | File storage path inside container |

---

## CI/CD (GitHub Actions)

`.github/workflows/ci.yml` runs on every push/PR to `main` or `develop`:

1. **backend-test** — installs deps, runs pytest with `--cov-fail-under=95`
2. **frontend-test** — installs deps, runs vitest with coverage
3. **docker-build** — builds and pushes images to Docker Hub (main branch only)

Required GitHub repository secrets:
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`

---

## Project Structure

```
doc-qa-app/
├── backend/
│   ├── app/
│   │   ├── api/            # Route handlers (auth, documents, chat)
│   │   ├── core/           # Config, security, database connections
│   │   ├── models/         # Pydantic schemas
│   │   ├── services/       # document, vector, chat, cache logic
│   │   └── tests/          # pytest test suite (65 tests, 96%+ coverage)
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   ├── pytest.ini
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/     # AuthPage, Dashboard, ChatPanel, MediaPlayer, etc.
│   │   ├── store/          # Zustand (authStore, docStore)
│   │   ├── services/       # Axios API client
│   │   └── test/           # Vitest test suite
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
├── .github/workflows/ci.yml
└── .gitignore
```

---

## Live Demo & Walkthrough Video

> **Demo URL:** _add your YouTube / Google Drive link here_

Walkthrough covers:
1. Register & login
2. Upload PDF → summary appears → ask questions via chat
3. Upload audio/video → transcript segments → ask question → click "Play at X:XX"
4. Docker Compose startup
5. GitHub Actions CI/CD pipeline

---

## AWS Deployment (Optional)

```bash
# Push to ECR
aws ecr create-repository --repository-name docqa-backend
aws ecr create-repository --repository-name docqa-frontend

# Deploy via ECS Fargate or App Runner
npm install -g @aws/copilot-cli
copilot init
```

Or deploy instantly on **Railway** or **Render** by connecting your GitHub repo.
