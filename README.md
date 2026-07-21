# AI Assistant - Step 1

Production-ready AI Assistant foundation with a ChatGPT-style interface powered by Groq API.

## Tech Stack

**Frontend:** React, Vite, Tailwind CSS, React Router, Axios, React Markdown
**Backend:** FastAPI, Python, LangChain, LangChain-Groq, Uvicorn

## Project Structure

```
.
├── backend/
│   ├── api/            # API route handlers
│   │   ├── __init__.py
│   │   └── chat.py     # POST /api/chat endpoint
│   ├── config/         # App configuration
│   │   ├── __init__.py
│   │   └── settings.py # Pydantic settings from env vars
│   ├── models/         # Pydantic schemas
│   │   ├── __init__.py
│   │   └── schemas.py  # ChatRequest, ChatResponse
│   ├── services/       # Business logic
│   │   ├── __init__.py
│   │   └── groq_service.py  # Groq LLM integration
│   ├── utils/          # Utilities
│   │   ├── __init__.py
│   │   └── logger.py   # Logging setup
│   ├── main.py         # FastAPI app entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/ # Reusable UI components
│   │   │   ├── ChatInput.jsx
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── Header.jsx
│   │   │   ├── LoadingIndicator.jsx
│   │   │   ├── MessageBubble.jsx
│   │   │   └── Sidebar.jsx
│   │   ├── hooks/      # Custom React hooks
│   │   │   └── useChat.js
│   │   ├── pages/      # Page components
│   │   │   └── ChatPage.jsx
│   │   ├── services/   # API service layer
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── vite.config.js
│   └── package.json
├── .env.example
├── Dockerfile
└── README.md
```

## Setup

### 1. Get a Groq API Key

Sign up at [console.groq.com](https://console.groq.com) and create an API key.

### 2. Environment Variables

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 3. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python main.py
```

Backend runs at http://localhost:8000

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173

## API

### POST /api/chat

**Request:**
```json
{ "message": "Hello" }
```

**Response:**
```json
{ "response": "Hello! How can I help you?" }
```

### GET /health

```json
{ "status": "ok", "version": "1.0.0" }
```

## What's Included

- ChatGPT-style dark UI with sidebar
- AI and user message bubbles
- Loading animation
- Responsive layout
- Markdown rendering in AI responses
- Environment-based configuration
- Structured logging
- Error handling
- CORS configuration
- Vite proxy for seamless dev experience

## What's NOT Included (Planned for later steps)

- Authentication
- Voice Assistant
- Memory / Chat History
- Redis
- ChromaDB / PostgreSQL
- LangGraph
- RAG / File Upload
- Tool Calling
- Multi-Agent System
