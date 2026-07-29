# Architecture

## System Overview

NovaAI follows a multi-tier architecture with a React frontend, FastAPI backend, and a LangGraph multi-agent system for AI processing.

```mermaid
graph TB
    subgraph Client ["Client Layer"]
        Browser[React SPA]
    end

    subgraph API ["API Layer (FastAPI)"]
        CORS[CORS Middleware]
        AuthMW[Auth Middleware]
        Routers[API Routers]
    end

    subgraph Agents ["Agent Layer (LangGraph)"]
        Supervisor[Supervisor]
        ChatAgent[Chat Agent]
        MemoryAgent[Memory Agent]
        RAGAgent[RAG Agent]
        ToolAgent[Tool Agent]
        PlanningAgent[Planning Agent]
        VoiceAgent[Voice Agent]
    end

    subgraph Data ["Data Layer"]
        SQLite[(SQLite)]
        ChromaDB[(ChromaDB)]
        Redis[(Redis / FakeRedis)]
    end

    subgraph External ["External Services"]
        Groq[Groq API]
        Whisper[Faster-Whisper]
        TTS[Edge TTS]
        WebSearch[Web Search API]
    end

    Browser --> CORS --> AuthMW --> Routers
    Routers --> Agents
    Routers --> SQLite
    Agents --> Groq
    Agents --> ChromaDB
    Agents --> Redis
    MemoryAgent --> ChromaDB
    MemoryAgent --> Redis
    RAGAgent --> ChromaDB
    ToolAgent --> WebSearch
    VoiceAgent --> Whisper
    VoiceAgent --> TTS
```

## Backend Architecture

### Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── config/settings.py      # Pydantic settings (env vars)
├── database/               # SQLAlchemy async engine, session, base
├── models/                 # ORM models (User, Conversation, Message, Document, Analytics)
├── schemas/                # Pydantic request/response schemas
├── api/                    # REST API routers (auth, chat, conversations, users)
├── auth/                   # JWT token creation/validation
├── agents/                 # 7 LangGraph agent nodes
├── graph/                  # Graph builder, state definition
├── services/               # Business logic (user, conversation, Groq LLM)
├── tools/                  # 8 LangChain tools + tool manager
├── memory/                 # Memory pipeline (manager, Redis service, ChromaDB service)
├── rag/                    # RAG pipeline (manager, document processing)
├── voice/                  # STT (Whisper), TTS (Edge), voice manager
├── analytics/              # Metrics, analytics service, router
├── middleware/              # Request ID, logging middleware
├── utils/                  # Logger, error tracker
└── requirements.txt
```

### Multi-Agent System (LangGraph)

NovaAI uses LangGraph to orchestrate 7 specialized agents in a directed graph:

```mermaid
graph LR
    Start[Entry] --> Supervisor
    Supervisor -->|memory request| MemoryAgent
    Supervisor -->|document query| RAGAgent
    Supervisor -->|tool needed| ToolAgent
    Supervisor -->|complex task| PlanningAgent
    Supervisor -->|voice input| VoiceAgent
    Supervisor -->|general chat| ChatAgent

    MemoryAgent --> ChatAgent
    RAGAgent --> ChatAgent
    ToolAgent --> ChatAgent
    PlanningAgent --> ChatAgent
    VoiceAgent --> ChatAgent
    ChatAgent --> END[End]
```

**State Flow:**
1. User message enters the graph as `AgentState`
2. **Supervisor** analyzes the message via Groq LLM and decides which agents to invoke (can be multiple)
3. Routed agents execute in sequence and enrich the state
4. **Chat Agent** always runs last to generate the final response
5. Graph terminates with `final_response` in state

#### Agent Descriptions

| Agent | Responsibility |
|-------|---------------|
| **Supervisor** | Routes messages to appropriate agents using LLM-based reasoning |
| **Chat Agent** | General conversation, greetings, natural language tasks |
| **Memory Agent** | Retrieves relevant memories from ChromaDB/Redis for context |
| **RAG Agent** | Fetches relevant document chunks from the knowledge base |
| **Tool Agent** | Executes tools (calculator, weather, search, etc.) via LangChain |
| **Planning Agent** | Breaks complex multi-step tasks into ordered plans |
| **Voice Agent** | Processes voice input (STT transcription, TTS response) |

### State Definition

The `AgentState` (TypedDict) carries data through the graph:

```python
class AgentState(TypedDict):
    user_message: str
    user_id: str
    conversation_id: int
    conversation_history: list[dict]
    routed_agents: list[str]
    retrieved_memories: list[dict]
    retrieved_documents: list[dict]
    final_response: str
    metadata: dict
    errors: list[str]
    voice_data: bytes | None
```

### Services

| Service | Purpose |
|---------|---------|
| `groq_service` | LLM inference via Groq API (chat completions, plain chat) |
| `conversation_service` | CRUD for conversations and messages |
| `user_service` | User registration, authentication, profile management |
| `memory_manager` | Orchestrates memory storage, retrieval, and search |
| `redis_service` | Redis cache wrapper with FakeRedis fallback |
| `chroma_service` | ChromaDB vector store operations |
| `rag_manager` | Document ingestion, chunking, embedding, querying |
| `voice_manager` | Full voice chat pipeline (STT → LLM → TTS) |
| `analytics_service` | Records chat metrics, traces, and errors |

## Frontend Architecture

### Project Structure

```
frontend/
├── src/
│   ├── main.jsx              # App entry point
│   ├── App.jsx               # Route definitions
│   ├── index.css             # Tailwind base styles
│   ├── pages/                # Page components
│   │   ├── LoginPage.jsx
│   │   ├── RegisterPage.jsx
│   │   ├── ChatPage.jsx
│   │   ├── VoicePage.jsx
│   │   ├── MemoryPage.jsx
│   │   ├── KnowledgeBasePage.jsx
│   │   ├── AnalyticsPage.jsx
│   │   └── ProfilePage.jsx
│   ├── components/           # Reusable UI components
│   │   ├── Header.jsx
│   │   ├── Sidebar.jsx
│   │   ├── ChatInput.jsx
│   │   ├── ChatWindow.jsx
│   │   ├── MessageBubble.jsx
│   │   ├── LoadingIndicator.jsx
│   │   └── ProtectedRoute.jsx
│   ├── hooks/                # Custom React hooks
│   │   ├── useChat.js
│   │   ├── useConversations.js
│   │   └── useVoice.js
│   ├── contexts/
│   │   └── AuthContext.jsx
│   └── services/
│       └── api.js            # Axios instance with interceptors
├── package.json
├── vite.config.js
├── tailwind.config.js
└── postcss.config.js
```

### Routing

| Path | Component | Auth Required |
|------|-----------|---------------|
| `/login` | LoginPage | No |
| `/register` | RegisterPage | No |
| `/` | ChatPage | Yes |
| `/c/:conversationId` | ChatPage | Yes |
| `/voice` | VoicePage | Yes |
| `/memory` | MemoryPage | Yes |
| `/knowledge` | KnowledgeBasePage | Yes |
| `/analytics` | AnalyticsPage | Yes |
| `/profile` | ProfilePage | Yes |

### Custom Hooks

| Hook | Purpose |
|------|---------|
| `useChat` | Manages chat state, message sending, conversation loading |
| `useConversations` | Fetches and manages conversation list |
| `useVoice` | Handles audio recording, transcription, voice chat |

### Auth Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend

    U->>F: Login (email + password)
    F->>B: POST /api/auth/login
    B-->>F: { access_token, refresh_token }
    F->>F: Store tokens in localStorage
    F->>F: Set AuthContext (isAuthenticated=true)

    loop Every Request
        F->>B: Authorization: Bearer <access_token>
        B->>B: Validate JWT
    end

    Note over F,B: On 401 Unauthorized
    F->>B: POST /api/auth/refresh { refresh_token }
    B-->>F: { access_token, refresh_token }
    F->>F: Update tokens, retry request
```

## Data Flow

### Chat Message Flow

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant API as FastAPI
    participant GS as Graph Supervisor
    participant AG as Agent Graph
    participant LLM as Groq LLM
    participant MEM as Memory Pipeline
    participant DB as SQLite

    U->>FE: Type message
    FE->>API: POST /api/chat { message, conversation_id? }
    API->>DB: Create/get conversation, save user message
    API->>MEM: Retrieve relevant memories
    API->>AG: Invoke graph with AgentState
    AG->>GS: Supervisor analyzes message
    GS-->>AG: Route decision (which agents)
    AG->>AG: Execute routed agents
    AG->>LLM: Generate final response (Chat Agent)
    LLM-->>AG: AI response
    AG-->>API: Complete state with final_response
    API->>DB: Save assistant message
    API->>MEM: Process both messages for memory
    API-->>FE: ChatResponse { response, conversation_id, tools_used }
    FE-->>U: Display response
```

## Database Schema

NovaAI uses SQLAlchemy async ORM with SQLite (swappable to PostgreSQL).

```mermaid
erDiagram
    User {
        int id PK
        string username UK
        string email UK
        string hashed_password
        string full_name
        string profile_picture
        bool is_active
        datetime created_at
        datetime updated_at
    }

    Conversation {
        int id PK
        int user_id FK
        string title
        datetime created_at
        datetime updated_at
    }

    Message {
        int id PK
        int conversation_id FK
        string role
        text content
        datetime created_at
    }

    Document {
        int id PK
        int user_id FK
        string filename
        string file_type
        int file_size
        int chunk_count
        string status
        string error_message
        datetime created_at
    }

    ChatMetric {
        int id PK
        string request_id
        string user_id
        int conversation_id
        int message_length
        int response_length
        float latency_ms
        bool success
        string agent_route
        json tools_used
        int memory_hits
        int rag_hits
        datetime created_at
    }

    ToolMetric {
        int id PK
        string request_id
        string tool_name
        json arguments
        float latency_ms
        bool success
        datetime created_at
    }

    PerformanceMetric {
        int id PK
        string request_id
        string endpoint
        string method
        int status_code
        float latency_ms
        datetime created_at
    }

    AgentTrace {
        int id PK
        string request_id
        string user_id
        int conversation_id
        json trace
        float total_latency_ms
        text supervisor_reasoning
        datetime created_at
    }

    ErrorLog {
        int id PK
        string request_id
        string error_type
        text error_message
        string endpoint
        datetime created_at
    }

    User ||--o{ Conversation : "has"
    User ||--o{ Document : "uploads"
    Conversation ||--o{ Message : "contains"
```

## Memory Pipeline

```mermaid
graph TD
    Msg[New Message] --> Extract[Extract Facts]
    Extract --> Score[Score Importance]
    Score -->|Above Threshold| Store[Store in ChromaDB]
    Score -->|Below Threshold| Skip[Skip]
    Store --> Embed[Generate Embedding]
    Embed --> Chroma[(ChromaDB)]
    Store --> Cache[(Redis Cache)]

    Query[Memory Query] --> Search[Semantic Search]
    Search --> Chroma
    Chroma --> Results[Top-K Results]
    Results --> Filter[Apply Similarity Threshold]
    Filter --> Output[Memory Results]
```

**Memory Categories:**
- `conversation` — Facts from conversation context
- `user_preference` — Detected user preferences
- `personal` — Personal information shared by the user

## RAG Pipeline

```mermaid
graph TD
    Upload[Upload Document] --> Validate[Validate File Type/Size]
    Validate --> Parse[Parse Document]
    Parse --> PDF{PDF?}
    PDF -->|Yes| PyPDF[Extract via pypdf]
    PDF -->|DOCX?| Docx[Extract via python-docx]
    PDF -->|TXT/MD| Text[Read as text]
    PyPDF --> Chunk[Split into Chunks]
    Docx --> Chunk
    Text --> Chunk
    Chunk --> Embed[Embed Chunks]
    Embed --> Store[Store in ChromaDB]
    Store --> DB[(ChromaDB: documents collection)]
    Store --> Meta[Save metadata to SQLite Document]

    Query[User Query] --> EmbedQ[Embed Query]
    EmbedQ --> Search[ChromaDB Similarity Search]
    Search --> DB
    DB --> Chunks[Relevant Chunks]
    Chunks --> Context[Build Context]
    Context --> LLM[Groq LLM: Generate Answer]
    LLM --> Answer[Response with Sources]
```

**Supported Formats:** PDF, DOCX, TXT, Markdown

**Chunking:** Configurable chunk size (default 800 chars) with overlap (default 200 chars).
