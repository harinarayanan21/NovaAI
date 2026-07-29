import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth.jwt import get_current_user
from backend.mcp.manager import mcp_manager
from backend.mcp.registry import registry
from backend.analytics.metrics import metrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])


class ConnectRequest(BaseModel):
    name: str


class DisconnectRequest(BaseModel):
    name: str


@router.get("/status")
async def get_mcp_status(_=Depends(get_current_user)):
    metrics.increment("mcp_requests")
    status = await mcp_manager.health()
    summary = registry.get_summary()
    return {**status, **summary}


@router.get("/servers")
async def get_mcp_servers(_=Depends(get_current_user)):
    metrics.increment("mcp_requests")
    servers = registry.get_servers()
    statuses = registry.get_status()
    return {
        "servers": [
            {
                "name": name,
                **info,
                "status": statuses.get(name, "unknown"),
            }
            for name, info in servers.items()
        ]
    }


@router.get("/tools")
async def get_mcp_tools(_=Depends(get_current_user)):
    metrics.increment("mcp_requests")
    tools = registry.get_all_tools_flat()
    return {"tools": tools, "total": len(tools)}


@router.post("/connect")
async def connect_mcp(req: ConnectRequest, _=Depends(get_current_user)):
    metrics.increment("mcp_requests")
    result = await mcp_manager.connect(req.name)
    if result.get("success"):
        return result
    raise HTTPException(status_code=400, detail=result.get("error", "Connection failed"))


@router.post("/disconnect")
async def disconnect_mcp(req: DisconnectRequest, _=Depends(get_current_user)):
    metrics.increment("mcp_requests")
    result = await mcp_manager.disconnect(req.name)
    if result.get("success"):
        return result
    raise HTTPException(status_code=400, detail=result.get("error", "Disconnect failed"))


@router.post("/refresh")
async def refresh_mcp(_=Depends(get_current_user)):
    metrics.increment("mcp_requests")
    results = await mcp_manager.refresh()
    return {"results": results, "total": len(results)}
