# API Reference

Base URL: `http://localhost:8000/api`

All authenticated endpoints require the `Authorization: Bearer <token>` header.

## Authentication

### Register

```
POST /api/auth/register
```

**Request:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecureP@ss123",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Login

```
POST /api/auth/login
```

**Request:**
```json
{
  "email": "john@example.com",
  "password": "SecureP@ss123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Refresh Token

```
POST /api/auth/refresh
```

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Logout

```
POST /api/auth/logout
```

**Response:** `204 No Content`

---

## Users

### Get Profile

```
GET /api/users/me
```

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "profile_picture": null,
  "is_active": true,
  "created_at": "2026-01-15T10:30:00Z"
}
```

### Update Profile

```
PUT /api/users/me
```

**Request:**
```json
{
  "full_name": "John Smith",
  "username": "johnsmith",
  "profile_picture": "https://example.com/avatar.jpg"
}
```

**Response (200):** Updated user object.

---

## Chat

### Send Message

```
POST /api/chat
```

**Headers:** `Authorization: Bearer <token>`

**Request:**
```json
{
  "message": "What is the weather in London?",
  "conversation_id": null
}
```

- `conversation_id`: Omit or pass `null` to start a new conversation. Pass an existing ID to continue a conversation.

**Response (200):**
```json
{
  "response": "The current weather in London is cloudy with a temperature of 15°C...",
  "conversation_id": 42,
  "tools_used": [
    {
      "tool_name": "get_weather",
      "arguments": {"location": "London"},
      "result_summary": "Weather: cloudy, 15°C"
    }
  ]
}
```

---

## Conversations

### List Conversations

```
GET /api/conversations
```

**Response (200):**
```json
[
  {
    "id": 42,
    "title": "Weather in London",
    "created_at": "2026-07-23T10:30:00Z",
    "updated_at": "2026-07-23T10:35:00Z"
  }
]
```

### Create Conversation

```
POST /api/conversations
```

**Request:**
```json
{
  "title": "My New Conversation"
}
```

**Response (201):** Conversation object.

### Get Conversation

```
GET /api/conversations/{conversation_id}
```

**Response (200):** Conversation object.

### Update Conversation

```
PUT /api/conversations/{conversation_id}
```

**Request:**
```json
{
  "title": "Updated Title"
}
```

### Delete Conversation

```
DELETE /api/conversations/{conversation_id}
```

**Response (200):**
```json
{ "detail": "Conversation deleted." }
```

### Get Messages

```
GET /api/conversations/{conversation_id}/messages
```

**Response (200):**
```json
[
  {
    "id": 1,
    "role": "user",
    "content": "Hello!",
    "created_at": "2026-07-23T10:30:00Z"
  },
  {
    "id": 2,
    "role": "assistant",
    "content": "Hello! How can I help you today?",
    "created_at": "2026-07-23T10:30:01Z"
  }
]
```

### Add Message

```
POST /api/conversations/{conversation_id}/messages
```

**Request:**
```json
{
  "content": "Tell me a joke"
}
```

---

## Memory

### List Memories

```
GET /api/memory?category=conversation
```

**Query Parameters:**
- `category` (optional): Filter by category (`conversation`, `user_preference`, `personal`)

**Response (200):**
```json
[
  {
    "id": "mem_abc123",
    "content": "User prefers dark mode",
    "metadata": {"category": "user_preference", "user_id": "1"},
    "similarity": null
  }
]
```

### Search Memories

```
POST /api/memory/search
```

**Request:**
```json
{
  "query": "What does the user prefer?",
  "category": "user_preference"
}
```

**Response (200):** List of memories with similarity scores.

### Get Memory Stats

```
GET /api/memory/stats
```

**Response (200):**
```json
{
  "total": 42,
  "categories": {"conversation": 30, "user_preference": 10, "personal": 2},
  "redis_available": true,
  "redis_fallback": false,
  "chromadb_available": true,
  "embedding_model": "BAAI/bge-small-en-v1.5"
}
```

### Delete Memory

```
DELETE /api/memory/{memory_id}
```

### Clear All Memories

```
DELETE /api/memory
```

---

## Voice

### Transcribe Audio

```
POST /api/voice/transcribe
```

**Request:**
```json
{
  "audio": "<base64-encoded-audio>",
  "filename": "recording.wav",
  "language": "en"
}
```

**Response (200):**
```json
{
  "text": "What is the weather today?",
  "language": "en",
  "duration": 2.5
}
```

### Text to Speech

```
POST /api/voice/speak
```

**Request:**
```json
{
  "text": "Hello, how can I help you?",
  "voice": "en-US-GuyNeural",
  "rate": "+0%",
  "volume": "+0%"
}
```

**Response (200):**
```json
{
  "audio": "<base64-encoded-mp3>",
  "format": "mp3",
  "size_bytes": 24000
}
```

### Voice Chat (Full Pipeline)

```
POST /api/voice/chat
```

**Request:**
```json
{
  "audio": "<base64-encoded-audio>",
  "filename": "recording.wav",
  "language": "en",
  "conversation_id": null,
  "voice": "en-US-GuyNeural",
  "auto_play": true
}
```

**Response (200):**
```json
{
  "transcription": "What is 2+2?",
  "response_text": "2 + 2 = 4",
  "conversation_id": 42,
  "response_audio": "<base64-encoded-mp3>",
  "audio_format": "mp3"
}
```

### Voice Chat Upload

```
POST /api/voice/chat/upload
```

Multipart form upload instead of base64.

**Form Fields:**
- `file` (file): Audio file
- `language` (optional): Language code
- `conversation_id` (optional): Existing conversation ID
- `voice` (optional): TTS voice name
- `auto_play` (optional, default: true)

### Get Voice Settings

```
GET /api/voice/settings
```

**Response (200):**
```json
{
  "stt_model": "tiny",
  "stt_device": "cpu",
  "stt_language": "en",
  "tts_voice": "en-US-GuyNeural",
  "tts_rate": "+0%",
  "tts_volume": "+0%",
  "available_voices": [...],
  "voice_enabled": true,
  "max_audio_size_mb": 25,
  "max_audio_duration_sec": 120
}
```

### List Voices

```
GET /api/voice/voices?language=en
```

### Voice Status

```
GET /api/voice/status
```

**Response (200):**
```json
{
  "stt_available": true,
  "tts_available": true,
  "stt_model": "faster-whisper",
  "tts_engine": "edge-tts"
}
```

---

## RAG (Knowledge Base)

### Upload Document

```
POST /api/rag/upload
```

Multipart form upload.

**Form Fields:**
- `file` (file): PDF, DOCX, TXT, or Markdown file

**Response (200):**
```json
{
  "document_id": 5,
  "filename": "my_report.pdf",
  "chunk_count": 24,
  "total_chars": 19200,
  "status": "completed"
}
```

### List Documents

```
GET /api/rag/documents
```

**Response (200):**
```json
[
  {
    "id": 5,
    "filename": "my_report.pdf",
    "file_type": "pdf",
    "file_size": 524288,
    "chunk_count": 24,
    "status": "completed",
    "error_message": null,
    "created_at": "2026-07-23T10:30:00Z"
  }
]
```

### Query Documents

```
POST /api/rag/query
```

**Request:**
```json
{
  "question": "What are the main findings?",
  "n_results": 5
}
```

**Response (200):**
```json
{
  "answer": "The main findings indicate that...",
  "sources": [
    {
      "document_id": 5,
      "filename": "my_report.pdf",
      "chunk_index": 3,
      "content": "...relevant text chunk...",
      "similarity": 0.89
    }
  ]
}
```

### Delete Document

```
DELETE /api/rag/document/{document_id}
```

### RAG Stats

```
GET /api/rag/stats
```

**Response (200):**
```json
{
  "total_documents": 5,
  "total_chunks": 120,
  "by_type": {"pdf": 3, "txt": 1, "docx": 1}
}
```

---

## Analytics

### Overview

```
GET /api/analytics/overview?days=7
```

**Query Parameters:**
- `days` (optional, default: 7, range: 1-90)

**Response (200):**
```json
{
  "total_requests": 1542,
  "total_chats": 1200,
  "avg_latency_ms": 850.5,
  "db_total_chats": 1200,
  "db_successful": 1180,
  "db_failed": 20,
  "db_avg_latency_ms": 850.5,
  "db_avg_message_length": 145.2,
  "db_avg_response_length": 320.8,
  "db_total_memory_hits": 856,
  "db_total_rag_hits": 234,
  "daily_breakdown": [
    {
      "date": "2026-07-23",
      "chats": 45,
      "success": 44,
      "failed": 1,
      "avg_latency_ms": 820.3,
      "tools": 12
    }
  ]
}
```

### Tool Analytics

```
GET /api/analytics/tools
```

### Performance

```
GET /api/analytics/performance
```

### History

```
GET /api/analytics/history?limit=50&offset=0
```

### Traces

```
GET /api/analytics/traces?limit=20
```

### Errors

```
GET /api/analytics/errors?limit=50
```

---

## Health Check

```
GET /health
```

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "checks": {
    "database": {"status": "ok"},
    "redis": {"status": "ok", "fallback": true},
    "chromadb": {"status": "ok"},
    "langgraph": {"status": "ok", "nodes": 7},
    "voice": {"status": "ok", "enabled": true},
    "rag": {"status": "ok", "collection": "documents"},
    "tool_manager": {"status": "ok", "tool_count": 8},
    "analytics": {"status": "ok", "total_requests": 1542},
    "groq": {"status": "configured", "model": "llama-3.3-70b-versatile"}
  }
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request — Invalid input or validation error |
| 401 | Unauthorized — Missing or invalid JWT token |
| 403 | Forbidden — Insufficient permissions |
| 404 | Not Found — Resource does not exist |
| 409 | Conflict — Username/email already taken |
| 413 | Payload Too Large — File exceeds size limit |
| 429 | Too Many Requests — Rate limit / service high demand |
| 500 | Internal Server Error — Unexpected server failure |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong."
}
```
