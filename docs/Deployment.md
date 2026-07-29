# Deployment Guide

## Docker Deployment (Recommended)

### Prerequisites

- Docker Engine 20.10+
- Docker Compose v2+
- A Groq API key

### Steps

1. **Clone the repository:**
   ```bash
   git clone <repo-url> && cd novaai
   ```

2. **Create environment file:**
   ```bash
   cp backend/.env.example backend/.env
   ```
   Edit `backend/.env` and set at minimum:
   ```
   GROQ_API_KEY=gsk_your_key_here
   JWT_SECRET_KEY=use-a-strong-random-secret
   ```

3. **Build and start services:**
   ```bash
   docker compose up -d --build
   ```

4. **Verify health:**
   ```bash
   curl http://localhost:8000/health
   ```

### Service Architecture

| Service | Port | Description |
|---------|------|-------------|
| `frontend` | 80 | Nginx-served React app |
| `backend` | 8000 | FastAPI application |
| `redis` | 6379 | Optional — enable with `--profile with-redis` |

### With Redis

Redis provides persistent caching. Without it, NovaAI falls back to FakeRedis (in-memory).

```bash
docker compose --profile with-redis up -d --build
```

### Volumes

| Volume | Purpose |
|--------|---------|
| `backend-data` | SQLite database persistence |
| `chroma-data` | ChromaDB vector store persistence |

### Logs

```bash
# All services
docker compose logs -f

# Backend only
docker compose logs -f backend

# Frontend only
docker compose logs -f frontend
```

### Stopping

```bash
docker compose down
```

To remove volumes (clears all data):
```bash
docker compose down -v
```

---

## Manual Deployment

### Backend

1. **Create a virtual environment:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run the server:**
   ```bash
   # Development (auto-reload)
   uvicorn main:app --reload --host 0.0.0.0 --port 8000

   # Production
   uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

### Frontend

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Development server:**
   ```bash
   npm run dev
   ```

3. **Production build:**
   ```bash
   npm run build
   # Serve the dist/ folder with any static file server
   ```

---

## Environment Variables

All environment variables are defined in `backend/config/settings.py`. Copy `.env.example` to `.env` and configure:

### Required

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Your Groq API key from [console.groq.com](https://console.groq.com/) |

### LLM Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model identifier |
| `GROQ_TEMPERATURE` | `0.7` | Sampling temperature (0-2) |
| `GROQ_MAX_TOKENS` | `1024` | Maximum tokens per response |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./ai_assistant.db` | SQLAlchemy async database URL |

For PostgreSQL, change to:
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/novaai
```

### JWT Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | `change-me-in-production` | Secret for signing JWT tokens |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |

### Redis

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `REDIS_USE_FAKE` | `true` | Use FakeRedis when Redis is unavailable |
| `REDIS_CACHE_TTL` | `86400` | Cache TTL in seconds (24h) |

### Memory (ChromaDB)

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORY_ENABLED` | `true` | Enable/disable memory pipeline |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | ChromaDB storage directory |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | FastEmbed embedding model |
| `MEMORY_SIMILARITY_THRESHOLD` | `0.6` | Minimum similarity score for retrieval |

### Voice

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_ENABLED` | `true` | Enable voice features |
| `WHISPER_MODEL` | `tiny` | Faster-Whisper model (`tiny`, `base`, `small`, `medium`) |
| `WHISPER_DEVICE` | `cpu` | Compute device (`cpu`, `cuda`) |
| `TTS_VOICE` | `en-US-GuyNeural` | Edge TTS voice identifier |

### RAG

| Variable | Default | Description |
|----------|---------|-------------|
| `RAG_CHUNK_SIZE` | `800` | Document chunk size (chars) |
| `RAG_CHUNK_OVERLAP` | `200` | Chunk overlap (chars) |
| `RAG_MAX_FILE_SIZE_MB` | `20` | Maximum upload file size |
| `RAG_COLLECTION` | `documents` | ChromaDB collection name for RAG |

---

## Production Checklist

### Security

- [ ] Set a strong, random `JWT_SECRET_KEY` (minimum 32 characters)
- [ ] Set `DEBUG=False`
- [ ] Use HTTPS (via reverse proxy: nginx, Caddy, etc.)
- [ ] Restrict `CORS_ORIGINS` to your domain
- [ ] Use PostgreSQL instead of SQLite for production
- [ ] Set up proper Redis with authentication

### Performance

- [ ] Use `--workers 4` (or CPU count) for Uvicorn
- [ ] Enable Redis for caching (set `REDIS_USE_FAKE=false`)
- [ ] Use a production-grade Whisper model (`small` or `medium`) if GPU is available
- [ ] Set up a CDN for frontend static assets

### Reliability

- [ ] Configure Docker health checks (included in `docker-compose.yml`)
- [ ] Set up log aggregation (e.g., ELK, Datadog)
- [ ] Configure database backups
- [ ] Set up monitoring and alerting

### Infrastructure

- [ ] Use a reverse proxy (nginx/Caddy) for TLS termination
- [ ] Configure firewall rules
- [ ] Set up automated backups for `chroma-data` and `backend-data` volumes
- [ ] Use Docker secrets or a vault for sensitive environment variables

---

## Monitoring

### Health Endpoint

```bash
curl http://localhost:8000/health
```

Returns status of all subsystems: database, Redis, ChromaDB, LangGraph, voice, RAG, tools, analytics, and Groq.

### Analytics API

The built-in analytics system tracks:
- Chat metrics (latency, success/failure, tool usage)
- Tool execution performance
- Agent traces (per-node latency, routing decisions)
- Error logs with stack traces

Access via `/api/analytics/overview`, `/api/analytics/tools`, `/api/analytics/performance`, `/api/analytics/traces`, `/api/analytics/errors`.

### Docker Health Checks

Both `backend` and `frontend` services include health checks:

- **Backend:** HTTP GET to `/health` every 30s
- **Frontend:** HTTP GET to `/` every 30s

### Logs

Backend logs are written to stdout/stderr and can be viewed via:
```bash
docker compose logs -f --tail=100 backend
```

---

## Updating

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose up -d --build

# Or for manual deployment
cd backend && pip install -r requirements.txt
cd frontend && npm install && npm run build
```
