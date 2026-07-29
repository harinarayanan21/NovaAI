import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from backend.config.settings import settings
from backend.memory.embedding_service import embedding_service
from backend.rag.document_loader import load_document
from backend.rag.document_chunker import chunk_text
from backend.rag.document_service import document_service
from backend.services.groq_service import groq_service

logger = logging.getLogger(__name__)

RAG_COLLECTION = "documents"


class RAGManager:
    """Orchestrates the RAG pipeline: upload, chunk, embed, store, query."""

    def __init__(self):
        self._client = None
        self._collection = None

    def _get_client(self):
        """Lazy-initialize ChromaDB client for documents."""
        if self._client is not None:
            return self._client
        try:
            import chromadb
            self._client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
            logger.info("RAG ChromaDB client initialized")
            return self._client
        except Exception as e:
            logger.error("Failed to initialize RAG ChromaDB: %s", str(e))
            raise

    def _get_collection(self):
        """Get or create the documents collection."""
        if self._collection is not None:
            return self._collection
        try:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=RAG_COLLECTION,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("RAG collection ready (count=%d)", self._collection.count())
            return self._collection
        except Exception as e:
            logger.error("Failed to get RAG collection: %s", str(e))
            raise

    async def upload_document(
        self,
        user_id: int,
        filename: str,
        file_content: bytes,
    ) -> dict:
        """Full upload pipeline: extract -> clean -> chunk -> embed -> store.

        Returns:
            dict with document_id, filename, chunk_count, status.
        """
        file_type = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"

        # Create document record
        doc = await document_service.create(
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            file_size=len(file_content),
            status="processing",
        )

        try:
            # 1. Extract text
            text = load_document(file_content, filename)
            logger.info("Extracted %d chars from %s", len(text), filename)

            # 2. Chunk text
            chunks = chunk_text(
                text,
                chunk_size=settings.RAG_CHUNK_SIZE,
                chunk_overlap=settings.RAG_CHUNK_OVERLAP,
            )
            if not chunks:
                await document_service.update_status(
                    doc.id, "failed", error_message="No content to index"
                )
                return {
                    "document_id": doc.id,
                    "filename": filename,
                    "chunk_count": 0,
                    "status": "failed",
                    "error": "No content to index",
                }

            # 3. Generate embeddings and store in ChromaDB
            embeddings = await embedding_service.embed(chunks)
            collection = self._get_collection()

            ids = []
            metadatas = []
            for i, chunk in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                ids.append(chunk_id)
                metadatas.append(
                    {
                        "user_id": str(user_id),
                        "document_id": str(doc.id),
                        "filename": filename,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "upload_time": datetime.now(timezone.utc).isoformat(),
                    }
                )

            # Batch add to ChromaDB (max 100 per batch)
            batch_size = 100
            for start in range(0, len(ids), batch_size):
                end = min(start + batch_size, len(ids))
                collection.add(
                    ids=ids[start:end],
                    embeddings=embeddings[start:end],
                    documents=chunks[start:end],
                    metadatas=metadatas[start:end],
                )

            # 4. Update document record
            await document_service.update_status(
                doc.id, "ready", chunk_count=len(chunks)
            )

            logger.info(
                "Document indexed: id=%d filename=%s chunks=%d",
                doc.id,
                filename,
                len(chunks),
            )

            return {
                "document_id": doc.id,
                "filename": filename,
                "chunk_count": len(chunks),
                "total_chars": len(text),
                "status": "ready",
            }

        except Exception as e:
            logger.error("Upload failed for %s: %s", filename, str(e))
            await document_service.update_status(
                doc.id, "failed", error_message=str(e)[:1000]
            )
            return {
                "document_id": doc.id,
                "filename": filename,
                "chunk_count": 0,
                "status": "failed",
                "error": str(e)[:500],
            }

    async def query(
        self,
        user_id: int,
        question: str,
        n_results: int = 5,
    ) -> dict:
        """Query documents using RAG: search relevant chunks, build context, ask Groq.

        Returns:
            dict with answer, sources (list of chunk metadata).
        """
        try:
            collection = self._get_collection()
            query_embedding = await embedding_service.embed_single(question)

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where={"user_id": str(user_id)},
                include=["documents", "metadatas", "distances"],
            )

            sources = []
            context_parts = []
            if results["ids"] and results["ids"][0]:
                for i, chunk_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i]
                    similarity = 1 - distance
                    doc_text = results["documents"][0][i]
                    meta = results["metadatas"][0][i]

                    sources.append(
                        {
                            "chunk_id": chunk_id,
                            "content": doc_text,
                            "filename": meta.get("filename", "unknown"),
                            "chunk_index": meta.get("chunk_index", 0),
                            "total_chunks": meta.get("total_chunks", 0),
                            "similarity": round(similarity, 4),
                        }
                    )
                    context_parts.append(
                        f"[Source: {meta.get('filename', 'unknown')}, "
                        f"chunk {meta.get('chunk_index', 0)+1}/"
                        f"{meta.get('total_chunks', 0)}]\n{doc_text}"
                    )

            if not context_parts:
                return {
                    "answer": "No relevant documents found for your question. Please upload documents first.",
                    "sources": [],
                }

            system_prompt = (
                "You are a helpful assistant that answers questions based on "
                "the provided document context. Use only the information in the "
                "context to answer. If the context does not contain enough "
                "information, say so clearly. Always cite which document or "
                "chunk your answer comes from when possible.\n\n"
                "## Document Context\n\n"
                + "\n\n---\n\n".join(context_parts)
            )

            answer, _tools = await groq_service.chat(
                question,
                history=None,
                system_prompt=system_prompt,
            )

            return {"answer": answer, "sources": sources}

        except Exception as e:
            logger.error("RAG query error: %s", str(e))
            raise

    async def delete_document(self, user_id: int, document_id: int) -> bool:
        """Delete a document and all its chunks from ChromaDB and SQLite."""
        try:
            collection = self._get_collection()
            results = collection.get(
                where={
                    "$and": [
                        {"user_id": str(user_id)},
                        {"document_id": str(document_id)},
                    ]
                },
                include=["metadatas"],
            )

            if results["ids"]:
                collection.delete(ids=results["ids"])
                logger.info("Deleted %d chunks for document %d", len(results["ids"]), document_id)

            deleted = await document_service.delete(document_id, user_id)
            return deleted

        except Exception as e:
            logger.error("Failed to delete document %d: %s", document_id, str(e))
            return False

    async def list_documents(self, user_id: int) -> list[dict]:
        """List all documents for a user with metadata."""
        docs = await document_service.list_user_documents(user_id)
        return [
            {
                "id": doc.id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "chunk_count": doc.chunk_count,
                "status": doc.status,
                "error_message": doc.error_message,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
            }
            for doc in docs
        ]

    async def get_stats(self, user_id: int) -> dict:
        """Get RAG statistics for a user."""
        doc_stats = await document_service.get_user_stats(user_id)
        return {
            **doc_stats,
            "collection_count": self._get_collection().count() if self._collection else 0,
        }

    async def ping(self) -> bool:
        """Check if the RAG ChromaDB collection is accessible."""
        try:
            client = self._get_client()
            client.heartbeat()
            return True
        except Exception:
            return False


rag_manager = RAGManager()
