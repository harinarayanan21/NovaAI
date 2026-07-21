import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from backend.config.settings import settings
from backend.memory.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class ChromaService:
    """ChromaDB service for long-term semantic memory."""

    def __init__(self):
        self._client = None
        self._collection = None

    def _get_client(self):
        """Lazy-initialize ChromaDB client."""
        if self._client is not None:
            return self._client
        try:
            import chromadb
            self._client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
            logger.info("ChromaDB initialized at %s", settings.CHROMA_PERSIST_DIR)
            return self._client
        except Exception as e:
            logger.error("Failed to initialize ChromaDB: %s", str(e))
            raise

    def _get_collection(self):
        """Get or create the memories collection."""
        if self._collection is not None:
            return self._collection
        try:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                "ChromaDB collection '%s' ready (count=%d)",
                settings.CHROMA_COLLECTION,
                self._collection.count(),
            )
            return self._collection
        except Exception as e:
            logger.error("Failed to get ChromaDB collection: %s", str(e))
            raise

    async def add_memory(
        self,
        user_id: str,
        content: str,
        category: str = "general",
        conversation_id: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[str]:
        """Store a memory in ChromaDB with embedding."""
        try:
            collection = self._get_collection()
            embedding = await embedding_service.embed_single(content)
            memory_id = str(uuid.uuid4())
            meta = {
                "user_id": str(user_id),
                "category": category,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            if conversation_id is not None:
                meta["conversation_id"] = str(conversation_id)
            if metadata:
                meta.update(metadata)

            collection.add(
                ids=[memory_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[meta],
            )
            logger.info("Memory stored: id=%s category=%s", memory_id, category)
            return memory_id
        except Exception as e:
            logger.error("ChromaDB add_memory error: %s", str(e))
            return None

    async def search_memories(
        self,
        user_id: str,
        query: str,
        n_results: int = 10,
        category: Optional[str] = None,
    ) -> list[dict]:
        """Search memories by semantic similarity."""
        try:
            collection = self._get_collection()
            query_embedding = await embedding_service.embed_single(query)
            where_filter = {"user_id": str(user_id)}
            if category:
                where_filter["category"] = category

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )

            memories = []
            if results["ids"] and results["ids"][0]:
                for i, memory_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i]
                    similarity = 1 - distance  # Convert cosine distance to similarity
                    if similarity >= settings.MEMORY_SIMILARITY_THRESHOLD:
                        memories.append({
                            "id": memory_id,
                            "content": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "similarity": round(similarity, 4),
                        })
            return memories
        except Exception as e:
            logger.error("ChromaDB search_memories error: %s", str(e))
            return []

    async def get_user_memories(
        self,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get all memories for a user, optionally filtered by category."""
        try:
            collection = self._get_collection()
            where_filter = {"user_id": str(user_id)}
            if category:
                where_filter["category"] = category

            results = collection.get(
                where=where_filter,
                include=["documents", "metadatas"],
                limit=limit,
            )

            memories = []
            if results["ids"]:
                for i, memory_id in enumerate(results["ids"]):
                    memories.append({
                        "id": memory_id,
                        "content": results["documents"][i],
                        "metadata": results["metadatas"][i],
                    })
            return memories
        except Exception as e:
            logger.error("ChromaDB get_user_memories error: %s", str(e))
            return []

    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """Delete a specific memory (with user ownership check)."""
        try:
            collection = self._get_collection()
            # Verify ownership before deleting
            result = collection.get(
                ids=[memory_id],
                include=["metadatas"],
            )
            if not result["ids"] or result["metadatas"][0].get("user_id") != str(user_id):
                return False
            collection.delete(ids=[memory_id])
            logger.info("Memory deleted: id=%s", memory_id)
            return True
        except Exception as e:
            logger.error("ChromaDB delete_memory error: %s", str(e))
            return False

    async def delete_user_memories(self, user_id: str) -> bool:
        """Delete all memories for a user."""
        try:
            collection = self._get_collection()
            results = collection.get(
                where={"user_id": str(user_id)},
                include=["metadatas"],
            )
            if results["ids"]:
                collection.delete(ids=results["ids"])
                logger.info("Deleted %d memories for user %s", len(results["ids"]), user_id)
            return True
        except Exception as e:
            logger.error("ChromaDB delete_user_memories error: %s", str(e))
            return False

    async def get_memory_stats(self, user_id: str) -> dict:
        """Get memory statistics for a user."""
        try:
            collection = self._get_collection()
            results = collection.get(
                where={"user_id": str(user_id)},
                include=["metadatas"],
            )
            total = len(results["ids"]) if results["ids"] else 0
            categories = {}
            if results["metadatas"]:
                for meta in results["metadatas"]:
                    cat = meta.get("category", "general")
                    categories[cat] = categories.get(cat, 0) + 1
            return {"total": total, "categories": categories}
        except Exception as e:
            logger.error("ChromaDB get_memory_stats error: %s", str(e))
            return {"total": 0, "categories": {}}

    async def ping(self) -> bool:
        """Check if ChromaDB is accessible."""
        try:
            client = self._get_client()
            client.heartbeat()
            return True
        except Exception:
            return False


chroma_service = ChromaService()
