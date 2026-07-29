import logging
from backend.graph.state import AgentState

logger = logging.getLogger(__name__)


async def rag_agent_node(state: AgentState) -> dict:
    """RAG agent that retrieves relevant document chunks.

    Integrates with the existing rag_manager to search ChromaDB
    for relevant document chunks and inject them into the graph state.
    """
    try:
        from backend.rag.rag_manager import rag_manager

        user_id = int(state.get("user_id", 0))
        user_message = state.get("user_message", "")

        if not user_id:
            logger.warning("RAG agent: no user_id provided")
            return {
                "retrieved_documents": [],
                "metadata": {
                    **state.get("metadata", {}),
                    "rag_agent_completed": True,
                    "rag_agent_message": "No user_id",
                },
            }

        docs = await rag_manager.list_documents(user_id)
        if not docs:
            logger.info("RAG agent: no documents found for user %s", user_id)
            return {
                "retrieved_documents": [],
                "metadata": {
                    **state.get("metadata", {}),
                    "rag_agent_completed": True,
                    "rag_agent_message": "No documents in knowledge base",
                },
            }

        query_result = await rag_manager.query(
            user_id=user_id,
            question=user_message,
            n_results=5,
        )

        sources = query_result.get("sources", [])

        logger.info(
            "RAG agent: retrieved %d chunks from %d documents for user %s",
            len(sources),
            len(docs),
            user_id,
        )

        return {
            "retrieved_documents": sources,
            "metadata": {
                **state.get("metadata", {}),
                "rag_agent_source_count": len(sources),
                "rag_agent_doc_count": len(docs),
                "rag_agent_completed": True,
            },
        }

    except Exception as e:
        logger.error("RAG agent error: %s", str(e))
        return {
            "retrieved_documents": [],
            "errors": state.get("errors", []) + [f"rag_agent: {str(e)[:200]}"],
        }
