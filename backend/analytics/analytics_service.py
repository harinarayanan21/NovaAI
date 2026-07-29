import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.analytics import ChatMetric, ToolMetric, PerformanceMetric, AgentTrace, ErrorLog
from backend.analytics.metrics import metrics

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for persisting and querying analytics data."""

    async def record_chat(
        self,
        db: AsyncSession,
        request_id: str,
        user_id: str,
        conversation_id: int,
        message_length: int,
        response_length: int,
        latency_ms: float,
        success: bool,
        error_message: str | None = None,
        agent_route: str | None = None,
        tools_used: list | None = None,
        memory_hits: int = 0,
        rag_hits: int = 0,
    ):
        metric = ChatMetric(
            request_id=request_id,
            user_id=user_id,
            conversation_id=conversation_id,
            message_length=message_length,
            response_length=response_length,
            latency_ms=latency_ms,
            success=success,
            error_message=error_message,
            agent_route=agent_route,
            tools_used=tools_used or [],
            memory_hits=memory_hits,
            rag_hits=rag_hits,
        )
        db.add(metric)
        await db.flush()

        metrics.increment("total_requests")
        metrics.increment("chat_messages")
        metrics.record_latency("chat_latency", latency_ms)
        if memory_hits:
            metrics.increment("memory_retrievals", memory_hits)
        if rag_hits:
            metrics.increment("rag_queries", rag_hits)
        if tools_used:
            metrics.increment("tool_invocations", len(tools_used))
        if success:
            metrics.increment("successful_requests")
        else:
            metrics.increment("failed_requests")

    async def record_tool(
        self,
        db: AsyncSession,
        request_id: str,
        user_id: str,
        tool_name: str,
        arguments: dict | None,
        result_length: int,
        latency_ms: float,
        success: bool,
    ):
        metric = ToolMetric(
            request_id=request_id,
            tool_name=tool_name,
            arguments=arguments,
            result_length=result_length,
            latency_ms=latency_ms,
            success=success,
            user_id=user_id,
        )
        db.add(metric)
        await db.flush()
        metrics.increment(f"tool_{tool_name}")

    async def record_performance(
        self,
        db: AsyncSession,
        request_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: float,
        user_id: str | None = None,
    ):
        metric = PerformanceMetric(
            request_id=request_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            latency_ms=latency_ms,
            user_id=user_id,
        )
        db.add(metric)
        await db.flush()
        metrics.record_latency(f"latency_{endpoint}", latency_ms)

    async def record_trace(
        self,
        db: AsyncSession,
        request_id: str,
        user_id: str,
        conversation_id: int,
        trace: list,
        total_latency_ms: float,
        supervisor_reasoning: str | None = None,
    ):
        record = AgentTrace(
            request_id=request_id,
            user_id=user_id,
            conversation_id=conversation_id,
            trace=trace,
            total_latency_ms=total_latency_ms,
            supervisor_reasoning=supervisor_reasoning,
        )
        db.add(record)
        await db.flush()

    async def record_error(
        self,
        db: AsyncSession,
        request_id: str | None,
        error_type: str,
        error_message: str,
        stack_trace: str | None = None,
        endpoint: str | None = None,
        user_id: str | None = None,
    ):
        log = ErrorLog(
            request_id=request_id,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            endpoint=endpoint,
            user_id=user_id,
        )
        db.add(log)
        await db.flush()
        metrics.increment("failed_requests")

    async def get_overview(self, db: AsyncSession, days: int = 7) -> dict:
        since = datetime.now(timezone.utc) - timedelta(days=days)

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

        avg_latency_q = await db.execute(
            select(func.avg(ChatMetric.latency_ms))
        )
        avg_latency = round(avg_latency_q.scalar() or 0.0, 2)

        avg_msg_q = await db.execute(select(func.avg(ChatMetric.message_length)))
        avg_msg_len = round(avg_msg_q.scalar() or 0.0, 1)

        avg_resp_q = await db.execute(select(func.avg(ChatMetric.response_length)))
        avg_resp_len = round(avg_resp_q.scalar() or 0.0, 1)

        mem_q = await db.execute(select(func.sum(ChatMetric.memory_hits)))
        total_mem = mem_q.scalar() or 0

        rag_q = await db.execute(select(func.sum(ChatMetric.rag_hits)))
        total_rag = rag_q.scalar() or 0

        daily = await self._daily_breakdown(db, days)

        return {
            **metrics.get_overview(),
            "db_total_chats": total,
            "db_successful": success,
            "db_failed": failed,
            "db_avg_latency_ms": avg_latency,
            "db_avg_message_length": avg_msg_len,
            "db_avg_response_length": avg_resp_len,
            "db_total_memory_hits": int(total_mem),
            "db_total_rag_hits": int(total_rag),
            "daily_breakdown": daily,
        }

    async def _daily_breakdown(self, db: AsyncSession, days: int) -> list:
        rows = await db.execute(
            select(ChatMetric)
            .where(
                ChatMetric.created_at >= datetime.now(timezone.utc) - timedelta(days=days)
            )
        )
        by_date = {}
        for m in rows.scalars().all():
            d = m.created_at.strftime("%Y-%m-%d")
            if d not in by_date:
                by_date[d] = {"date": d, "chats": 0, "success": 0, "failed": 0, "avg_latency": 0.0, "tools": 0, "latencies": []}
            by_date[d]["chats"] += 1
            if m.success:
                by_date[d]["success"] += 1
            else:
                by_date[d]["failed"] += 1
            by_date[d]["latencies"].append(m.latency_ms)
            if m.tools_used:
                by_date[d]["tools"] += len(m.tools_used)

        result = []
        for d in sorted(by_date.keys()):
            v = by_date[d]
            lats = v.pop("latencies")
            v["avg_latency"] = round(sum(lats) / len(lats), 2) if lats else 0
            result.append(v)
        return result

    async def get_tool_analytics(self, db: AsyncSession) -> dict:
        stats = metrics.get_tool_stats()

        rows = await db.execute(
            select(ToolMetric.tool_name, func.count(ToolMetric.id), func.avg(ToolMetric.latency_ms))
            .group_by(ToolMetric.tool_name)
        )
        db_tools = {}
        for name, count, avg_lat in rows.all():
            db_tools[name] = {"count": count, "avg_latency_ms": round(avg_lat or 0, 2)}

        return {**stats, "db_tool_stats": db_tools}

    async def get_performance(self, db: AsyncSession) -> dict:
        stats = metrics.get_performance_stats()

        rows = await db.execute(
            select(
                PerformanceMetric.endpoint,
                func.count(PerformanceMetric.id),
                func.avg(PerformanceMetric.latency_ms),
            )
            .group_by(PerformanceMetric.endpoint)
        )
        db_endpoints = {}
        for ep, count, avg_lat in rows.all():
            db_endpoints[ep] = {"count": count, "avg_latency_ms": round(avg_lat or 0, 2)}

        return {**stats, "db_endpoints": db_endpoints}

    async def get_history(self, db: AsyncSession, limit: int = 50, offset: int = 0) -> list:
        rows = await db.execute(
            select(ChatMetric).order_by(ChatMetric.created_at.desc()).limit(limit).offset(offset)
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

    async def get_traces(self, db: AsyncSession, limit: int = 20) -> list:
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

    async def get_errors(self, db: AsyncSession, limit: int = 50) -> list:
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


analytics_service = AnalyticsService()
