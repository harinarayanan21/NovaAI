# MCP (Model Context Protocol) Integration

## Overview

Model Context Protocol (MCP) is a standard for connecting AI assistants to external
tools and services. NovaAI implements MCP as a client, allowing it to connect to
any MCP-compatible server (GitHub, Google Drive, databases, etc.) and use their
tools on behalf of the user.

## Architecture

```
User Message
    │
    ▼
Supervisor (detects MCP-related intent)
    │
    ▼
MCP Agent (LangGraph node)
    │
    ▼
MCP Manager
    ├── MCPServerClient (GitHub)
    ├── MCPServerClient (Google Drive)
    └── MCPServerClient (...)
          │
          ▼
MCP SDK (stdio transport)
    │
    ▼
External MCP Server (npx -y @modelcontextprotocol/server-xxx)
```

### Components

| Component | File | Purpose |
|-----------|------|---------|
| **Client** | `backend/mcp/client.py` | Single server connection (stdin/stdout transport) |
| **Registry** | `backend/mcp/registry.py` | Tracks servers, tools, capabilities, status |
| **Manager** | `backend/mcp/manager.py` | Orchestrates all server connections |
| **Router** | `backend/mcp/router.py` | FastAPI endpoints for MCP management |
| **Agent** | `backend/agents/mcp_agent.py` | LangGraph node that routes to MCP tools |
| **Frontend** | `frontend/src/pages/MCPPage.jsx` | UI for managing MCP servers |

## Configuration

Add MCP servers via the `MCP_SERVERS` environment variable — a JSON array of
server configurations:

```json
MCP_SERVERS='[
  {
    "name": "github",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"]
  },
  {
    "name": "google-drive",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-google-drive"]
  }
]'
```

Additional options:

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SERVERS` | `[]` | JSON array of server configs |
| `MCP_AUTO_CONNECT` | `true` | Connect all servers on startup |

## API Endpoints

All endpoints require authentication (JWT Bearer token).

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/mcp/status` | Overall MCP health and summary |
| `GET` | `/api/mcp/servers` | List all configured servers with status |
| `GET` | `/api/mcp/tools` | List all available tools across servers |
| `POST` | `/api/mcp/connect` | Connect to a server `{"name": "github"}` |
| `POST` | `/api/mcp/disconnect` | Disconnect from a server `{"name": "github"}` |
| `POST` | `/api/mcp/refresh` | Refresh tool lists for all connected servers |

## LangGraph Integration

The MCP agent is registered as a LangGraph node alongside the existing agents.
The supervisor detects MCP-related intent (e.g., "list my repos", "search drive")
and routes to the `mcp_agent` node. The MCP agent:

1. Inspects the user message
2. Uses Groq to decide which MCP tool to call
3. Executes the tool via the manager
4. Returns results into `tool_results` and `mcp_data` state fields

## Adding a New MCP Server

1. Install the MCP server package (usually via npx or pip)
2. Add it to `MCP_SERVERS` in your `.env` file
3. Restart the backend — the server appears in `/api/mcp/servers`
4. Connect via the UI or API: `POST /api/mcp/connect {"name": "..."}`

## Examples

**GitHub** — List repositories, read issues, manage PRs:
```json
{
  "name": "github",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"]
}
```

**Google Drive** — Search and read files:
```json
{
  "name": "google-drive",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-google-drive"]
}
```

**Gmail** — Read and search emails:
```json
{
  "name": "gmail",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-gmail"]
}
```

**Database (Postgres)** — Run queries:
```json
{
  "name": "postgres",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://..."]
}
```

## Health Check

The `/health` endpoint includes MCP status:
```json
{
  "mcp": {
    "status": "ok",
    "connected_servers": 2,
    "disconnected_servers": 0,
    "total_servers": 2,
    "total_tools": 24
  }
}
```

## Analytics

MCP usage is tracked in the metrics system:
- `mcp_requests` — total MCP API requests
- `mcp_tool_{name}` — per-tool invocation counter
- `mcp_{server}` — per-server latency tracking
