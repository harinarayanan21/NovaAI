# Contributing to NovaAI

Thank you for your interest in contributing to NovaAI! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- Git
- A [Groq API key](https://console.groq.com/)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

pip install -r requirements.txt

cp .env.example .env
# Edit .env — set GROQ_API_KEY

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend runs at `http://localhost:8000` with auto-reload. API docs at `http://localhost:8000/docs`.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` with hot module replacement.

## Project Structure

```
novaai/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── agents/              # LangGraph agent nodes
│   ├── graph/               # Graph builder and state
│   ├── api/                 # REST API routers
│   ├── tools/               # LangChain tools
│   ├── memory/              # Memory pipeline
│   ├── rag/                 # RAG pipeline
│   ├── voice/               # STT/TTS services
│   ├── analytics/           # Metrics and analytics
│   ├── services/            # Business logic
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic schemas
│   ├── auth/                # JWT utilities
│   ├── config/              # Application settings
│   ├── database/            # Database engine/session
│   ├── middleware/           # Request middleware
│   └── utils/               # Shared utilities
├── frontend/
│   └── src/
│       ├── pages/           # Route page components
│       ├── components/      # Reusable UI components
│       ├── hooks/           # Custom React hooks
│       ├── contexts/        # React contexts
│       └── services/        # API client
├── docs/                    # Documentation
├── docker-compose.yml
├── Dockerfile
└── LICENSE
```

## Code Style

### Python (Backend)

- Follow PEP 8 conventions
- Use type hints for function signatures
- Use async/await for all I/O operations
- Keep functions focused and under 50 lines where possible
- Use `logger` from `backend.utils.logger` for logging (not `print`)
- Use Pydantic models for request/response validation
- Prefix private/internal functions with `_`

### JavaScript/JSX (Frontend)

- Use functional components with hooks
- Use named exports for components
- Keep components under 200 lines
- Extract reusable logic into custom hooks
- Use Tailwind CSS for styling (no inline styles)

### General

- No hardcoded secrets or API keys
- No commented-out code blocks
- Write descriptive commit messages
- Keep dependencies minimal and justified

## Adding a New Tool

Tools are LangChain `BaseTool` instances registered in `backend/tools/tool_manager.py`.

1. Create a new file in `backend/tools/`:
   ```python
   from langchain_core.tools import tool

   @tool
   def my_new_tool(param: str) -> str:
       """Description of what this tool does."""
       # Implementation
       return result
   ```

2. Register in `backend/tools/tool_manager.py`:
   ```python
   from backend.tools.my_new_tool import my_new_tool

   ALL_TOOLS = [
       # ... existing tools ...
       my_new_tool,
   ]
   ```

3. The tool is automatically available to the Tool Agent and listed in the health check.

## Adding a New Agent

1. Create a new file in `backend/agents/`:
   ```python
   from backend.graph.state import AgentState

   async def my_agent_node(state: AgentState) -> dict:
       # Process state and return updates
       return {
           "metadata": {**state.get("metadata", {}), "my_data": result}
       }
   ```

2. Register in `backend/graph/graph_builder.py`:
   - Import the node function
   - Add via `graph.add_node("my_agent", my_agent_node)`
   - Add routing edges

3. Update the Supervisor prompt in `backend/agents/supervisor.py` to include the new agent.

## Testing

Run tests from the project root:

```bash
# Backend tests (if using pytest)
cd backend && pytest

# Frontend tests (if configured)
cd frontend && npm test
```

## Pull Request Process

1. **Fork and create a branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes** following the code style guidelines.

3. **Test your changes:**
   - Verify the backend starts without errors
   - Verify the frontend builds without errors
   - Test the affected API endpoints manually or via automated tests

4. **Commit with a clear message:**
   ```bash
   git commit -m "feat: add new weather tool for city forecasts"
   ```

   Use conventional commits:
   - `feat:` — New feature
   - `fix:` — Bug fix
   - `docs:` — Documentation changes
   - `refactor:` — Code refactoring
   - `test:` — Adding or updating tests
   - `chore:` — Maintenance tasks

5. **Push and create a Pull Request:**
   ```bash
   git push origin feature/my-feature
   ```

6. **In your PR:**
   - Describe what changed and why
   - Include screenshots for UI changes
   - Reference any related issues
   - Ensure no secrets or `.env` files are committed

## Adding a New Page (Frontend)

1. Create a new page in `frontend/src/pages/`:
   ```jsx
   export default function MyPage() {
     return <div>...</div>;
   }
   ```

2. Add a route in `frontend/src/App.jsx`:
   ```jsx
   <Route path="/my-page" element={
     <ProtectedRoute><MyPage /></ProtectedRoute>
   } />
   ```

3. Add a sidebar link in `frontend/src/components/Sidebar.jsx`.

## Adding a New API Endpoint

1. Create or extend a router in `backend/api/`:
   ```python
   router = APIRouter(prefix="/my-endpoint", tags=["my-tag"])

   @router.get("")
   async def my_endpoint(current_user: User = Depends(get_current_user)):
       return {"data": "..."}
   ```

2. Register in `backend/main.py`:
   ```python
   from backend.api.my_module import router as my_router
   app.include_router(my_router, prefix="/api")
   ```

## Questions?

Open an issue on GitHub for questions, bug reports, or feature requests.
