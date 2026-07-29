import logging
import traceback
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db
from backend.auth.jwt import get_current_user
from backend.analytics.metrics import metrics
from backend.models.analytics import ChatMetric, ToolMetric, PerformanceMetric, AgentTrace, ErrorLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def get_overview(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        total_q = await db.execute(select(func.count(ChatMetric.id)))
        total = total_q.scalar() or 0

        success_q = await db.execute(
            select(func.count(ChatMetric.id)).where(ChatMetric.success.is_(True))
        )
        success = success_q.scalar() or 0

        failed_q = await db.execute(
            select(func.count(ChatMetric.id)).where(ChatMetric.success.is_(False))
        )
        failed = failed_q.scalar() or 0

        avg_lat_q = await db.execute(select(func.avg(ChatMetric.latency_ms)))
        avg_lat = float(round(avg_lat_q.scalar() or 0.0, 2))

        avg_msg_q = await db.execute(select(func.avg(ChatMetric.message_length)))
        avg_msg_len = float(round(avg_msg_q.scalar() or 0.0, 1))

        avg_resp_q = await db.execute(select(func.avg(ChatMetric.response_length)))
        avg_resp_len = float(round(avg_resp_q.scalar() or 0.0, 1))

        mem_q = await db.execute(select(func.sum(ChatMetric.memory_hits)))
        total_mem = int(mem_q.scalar() or 0)

        rag_q = await db.execute(select(func.sum(ChatMetric.rag_hits)))
        total_rag = int(rag_q.scalar() or 0)

        since = datetime.now(timezone.utc) - timedelta(days=days)
        rows = await db.execute(
            select(ChatMetric).where(ChatMetric.created_at >= since)
        )
        by_date = {}
        for m in rows.scalars().all():
            d = m.created_at.strftime("%Y-%m-%d")
            if d not in by_date:
                by_date[d] = {
                    "date": d,
                    "chats": 0,
                    "success": 0,
                    "failed": 0,
                    "avg_latency": 0.0,
                    "tools": 0,
                    "latencies": [],
                }
            by_date[d]["chats"] += 1
            if m.success:
                by_date[d]["success"] += 1
            else:
                by_date[d]["failed"] += 1
            by_date[d]["latencies"].append(m.latency_ms)
            if m.tools_used:
                by_date[d]["tools"] += len(m.tools_used)

        daily = []
        for d in sorted(by_date.keys()):
            v = by_date[d]
            lats = v.pop("latencies")
            v["avg_latency"] = (
                float(round(sum(lats) / len(lats), 2)) if lats else 0.0
            )
            daily.append(v)

        return {
            **metrics.get_overview(),
            "db_total_chats": int(total),
            "db_successful": int(success),
            "db_failed": int(failed),
            "db_avg_latency_ms": avg_lat,
            "db_avg_message_length": avg_msg_len,
            "db_avg_response_length": avg_resp_len,
            "db_total_memory_hits": total_mem,
            "db_total_rag_hits": total_rag,
            "daily_breakdown": daily,
        }
    except Exception as e:
        logger.error("analytics overview failed: %s\n%s", e, traceback.format_exc())
        return {"error": str(e)}


@router.get("/tools")
async def get_tool_analytics(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        stats = metrics.get_tool_stats()
        rows = await db.execute(
            select(
                ToolMetric.tool_name,
                func.count(ToolMetric.id),
                func.avg(ToolMetric.latency_ms),
            ).group_by(ToolMetric.tool_name)
        )
        db_tools = {}
        for name, count, avg_lat in rows.all():
            db_tools[name] = {
                "count": int(count),
                "avg_latency_ms": float(round(avg_lat or 0, 2)),
            }
        return {**stats, "db_tool_stats": db_tools}
    except Exception as e:
        logger.error("analytics tools failed: %s\n%s", e, traceback.format_exc())
        return {"error": str(e)}


@router.get("/performance")
async def get_performance(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        stats = metrics.get_performance_stats()
        rows = await db.execute(
            select(
                PerformanceMetric.endpoint,
                func.count(PerformanceMetric.id),
                func.avg(PerformanceMetric.latency_ms),
            ).group_by(PerformanceMetric.endpoint)
        )
        db_endpoints = {}
        for ep, count, avg_lat in rows.all():
            db_endpoints[ep] = {
                "count": int(count),
                "avg_latency_ms": float(round(avg_lat or 0, 2)),
            }
        return {**stats, "db_endpoints": db_endpoints}
    except Exception as e:
        logger.error(
            "analytics performance failed: %s\n%s", e, traceback.format_exc()
        )
        return {"error": str(e)}


@router.get("/history")
async def get_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        rows = await db.execute(
            select(ChatMetric)
            .order_by(ChatMetric.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [
            {
                "id": m.id,
                "request_id": m.request_id,
                "user_id": m.user_id,
                "conversation_id": m.conversation_id,
                "message_length": m.message_length,
                "response_length": m.response_length,
                "latency_ms": m.latency_ms,
                "success": m.success,
                "agent_route": m.agent_route,
                "tools_used": m.tools_used or [],
                "memory_hits": m.memory_hits,
                "rag_hits": m.rag_hits,
                "created_at": m.created_at.isoformat(),
            }
            for m in rows.scalars().all()
        ]
    except Exception as e:
        logger.error("analytics history failed: %s\n%s", e, traceback.format_exc())
        return {"error": str(e)}


@router.get("/traces")
async def get_traces(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        rows = await db.execute(
            select(AgentTrace).order_by(AgentTrace.created_at.desc()).limit(limit)
        )
        return [
            {
                "id": t.id,
                "request_id": t.request_id,
                "trace": t.trace or [],
                "total_latency_ms": t.total_latency_ms,
                "supervisor_reasoning": t.supervisor_reasoning,
                "created_at": t.created_at.isoformat(),
            }
            for t in rows.scalars().all()
        ]
    except Exception as e:
        logger.error("analytics traces failed: %s\n%s", e, traceback.format_exc())
        return {"error": str(e)}


@router.get("/errors")
async def get_errors(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        rows = await db.execute(
            select(ErrorLog).order_by(ErrorLog.created_at.desc()).limit(limit)
        )
        return [
            {
                "id": e.id,
                "request_id": e.request_id,
                "error_type": e.error_type,
                "error_message": e.error_message,
                "endpoint": e.endpoint,
                "created_at": e.created_at.isoformat(),
            }
            for e in rows.scalars().all()
        ]
    except Exception as e:
        logger.error("analytics errors failed: %s\n%s", e, traceback.format_exc())
        return {"error": str(e)}
