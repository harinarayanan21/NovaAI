import time
import traceback
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.schemas import ChatRequest, ChatResponse, ToolCallInfo
from backend.services.conversation_service import conversation_service
from backend.memory.memory_manager import memory_manager
from backend.graph.state import create_initial_state
from backend.graph.graph_builder import graph_manager
from backend.auth.jwt import get_current_user
from backend.models.user import User
from backend.database.session import get_db
from backend.utils.logger import logger
from backend.analytics.analytics_service import analytics_service
from backend.utils.error_tracker import capture_exception

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    request_id = getattr(http_request.state, "request_id", "")
    start = time.perf_counter()
    conversation_id = 0
    tools_used_list = []
    memory_hits = 0
    rag_hits = 0

    try:
        logger.info("Message from %s: %s", current_user.username, request.message[:100])

        if request.conversation_id:
            conv = await conversation_service.get_conversation(
                db, request.conversation_id, current_user.id
            )
            if not conv:
                raise HTTPException(status_code=404, detail="Conversation not found.")
            conversation_id = conv.id
        else:
            title = await conversation_service.generate_title_from_message(
                request.message
            )
            conv = await conversation_service.create_conversation(
                db, current_user.id, title
            )
            conversation_id = conv.id

        http_request.state.conversation_id = conversation_id
        await conversation_service.add_message(db, conversation_id, "user", request.message)

        messages = await conversation_service.get_messages(db, conversation_id, current_user.id)
        history = [{"role": m.role, "content": m.content} for m in messages[:-1]] if messages else []

        initial_state = create_initial_state(
            user_message=request.message,
            user_id=str(current_user.id),
            conversation_id=conversation_id,
            conversation_history=history,
        )

        result = await graph_manager.invoke(initial_state)

        ai_response = result.get("final_response", "")
        if not ai_response:
            ai_response = "I'm sorry, I couldn't generate a response."

        await conversation_service.add_message(db, conversation_id, "assistant", ai_response)

        try:
            await memory_manager.process_message(
                str(current_user.id), conversation_id, "user", request.message
            )
            await memory_manager.process_message(
                str(current_user.id), conversation_id, "assistant", ai_response
            )
        except Exception as mem_err:
            logger.warning("Memory processing failed (non-fatal): %s", str(mem_err))

        metadata = result.get("metadata", {})
        agent_route = metadata.get("supervisor_agents", [])
        trace = metadata.get("agent_trace", [])

        http_request.state.agent_route = agent_route

        memory_hits = len(result.get("retrieved_memories", []))
        rag_hits = len(result.get("retrieved_documents", []))
        http_request.state.memory_hits = memory_hits
        http_request.state.rag_hits = rag_hits

        tool_call_infos = []
        for tc in metadata.get("chat_agent_tools_used", []):
            if isinstance(tc, dict):
                info = ToolCallInfo(
                    tool_name=tc.get("tool_name", "unknown"),
                    arguments=tc.get("arguments", {}),
                    result_summary=tc.get("result_summary"),
                )
                tool_call_infos.append(info)
                tool_call_infos_dict = {
                    "tool_name": tc.get("tool_name", "unknown"),
                    "arguments": tc.get("arguments", {}),
                }
                tools_used_list.append(tool_call_infos_dict)

        http_request.state.tool_calls = [t.tool_name for t in tool_call_infos]

        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        try:
            await analytics_service.record_chat(
                db=db,
                request_id=request_id,
                user_id=str(current_user.id),
                conversation_id=conversation_id,
                message_length=len(request.message),
                response_length=len(ai_response),
                latency_ms=latency_ms,
                success=True,
                agent_route=",".join(agent_route),
                tools_used=tools_used_list,
                memory_hits=memory_hits,
                rag_hits=rag_hits,
            )

            await analytics_service.record_trace(
                db=db,
                request_id=request_id,
                user_id=str(current_user.id),
                conversation_id=conversation_id,
                trace=trace,
                total_latency_ms=metadata.get("total_latency_ms", latency_ms),
                supervisor_reasoning=metadata.get("supervisor_reasoning"),
            )
        except Exception as ana_err:
            logger.warning("Analytics recording failed (non-fatal): %s", str(ana_err))

        return ChatResponse(
            response=ai_response,
            conversation_id=conversation_id,
            tools_used=tool_call_infos,
        )
    except HTTPException:
        raise
    except ValueError as e:
        error_message = str(e)
        logger.error("Configuration error: %s", error_message)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        try:
            err_data = capture_exception(e, request_id, "/api/chat", str(current_user.id))
            await analytics_service.record_error(
                db=db, request_id=request_id, **err_data
            )
            await analytics_service.record_chat(
                db=db, request_id=request_id, user_id=str(current_user.id),
                conversation_id=conversation_id, message_length=len(request.message),
                response_length=0, latency_ms=latency_ms, success=False,
                error_message=error_message,
            )
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Server configuration error.")
    except Exception as e:
        error_message = str(e)
        logger.error("Chat error: %s", error_message)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        try:
            err_data = capture_exception(e, request_id, "/api/chat", str(current_user.id))
            await analytics_service.record_error(
                db=db, request_id=request_id, **err_data
            )
            await analytics_service.record_chat(
                db=db, request_id=request_id, user_id=str(current_user.id),
                conversation_id=conversation_id, message_length=len(request.message),
                response_length=0, latency_ms=latency_ms, success=False,
                error_message=error_message,
            )
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Failed to generate response.")
