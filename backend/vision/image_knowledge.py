import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy import select, delete
from backend.config.settings import settings
from backend.database.session import async_session
from backend.memory.embedding_service import embedding_service
from backend.models.image import ImageRecord

logger = logging.getLogger(__name__)

VISION_COLLECTION = "vision_knowledge"


class ImageKnowledgeBase:
    """Stores and retrieves image embeddings (captions, OCR text) for semantic search."""

    def __init__(self):
        self._client = None
        self._collection = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        import chromadb
        self._client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        return self._client

    def _get_collection(self):
        if self._collection is not None:
            return self._collection
        client = self._get_client()
        self._collection = client.get_or_create_collection(
            name=VISION_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        return self._collection

    async def store_image(
        self,
        user_id: int,
        filename: str,
        stored_name: str,
        file_type: str,
        file_size: int,
        width: int,
        height: int,
        caption: str = "",
        ocr_text: str = "",
        description: str = "",
    ) -> ImageRecord:
        """Store image metadata in SQLite and embeddings in ChromaDB."""
        async with async_session() as db:
            record = ImageRecord(
                user_id=user_id,
                filename=filename,
                stored_name=stored_name,
                file_type=file_type,
                file_size=file_size,
                width=width,
                height=height,
                caption=caption[:2000] if caption else "",
                ocr_text=ocr_text[:10000] if ocr_text else "",
                description=description[:2000] if description else "",
            )
            db.add(record)
            await db.commit()
            await db.refresh(record)

        texts = []
        if caption:
            texts.append(f"[Caption] {caption}")
        if ocr_text:
            texts.append(f"[OCR] {ocr_text}")
        if description:
            texts.append(f"[Description] {description}")

        if texts:
            try:
                embeddings = await embedding_service.embed(texts)
                collection = self._get_collection()
                ids = [str(uuid.uuid4()) for _ in texts]
                metadatas = [
                    {
                        "user_id": str(user_id),
                        "image_id": str(record.id),
                        "filename": filename,
                        "type": "caption" if i == 0 and caption else ("ocr" if i == 1 and ocr_text else "description"),
                        "stored_name": stored_name,
                        "upload_time": datetime.now(timezone.utc).isoformat(),
                    }
                    for i in range(len(texts))
                ]
                collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                )
                logger.info("Stored %d embeddings for image %d", len(texts), record.id)
            except Exception as e:
                logger.warning("Failed to store image embeddings: %s", e)

        return record

    async def search(self, user_id: int, query: str, n_results: int = 10) -> list[dict]:
        """Semantic search across stored image knowledge."""
        try:
            query_embedding = await embedding_service.embed_single(query)
            collection = self._get_collection()
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where={"user_id": str(user_id)},
                include=["documents", "metadatas", "distances"],
            )
            hits = []
            if results["ids"] and results["ids"][0]:
                for i, chunk_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i]
                    hits.append({
                        "chunk_id": chunk_id,
                        "content": results["documents"][0][i],
                        "image_id": int(results["metadatas"][0][i].get("image_id", 0)),
                        "filename": results["metadatas"][0][i].get("filename", ""),
                        "type": results["metadatas"][0][i].get("type", ""),
                        "similarity": round(1 - distance, 4),
                    })
            return hits
        except Exception as e:
            logger.error("Image knowledge search error: %s", e)
            return []

    async def list_images(self, user_id: int) -> list[dict]:
        """List all images for a user."""
        async with async_session() as db:
            result = await db.execute(
                select(ImageRecord)
                .where(ImageRecord.user_id == user_id)
                .order_by(ImageRecord.created_at.desc())
            )
            return [
                {
                    "id": img.id,
                    "filename": img.filename,
                    "stored_name": img.stored_name,
                    "file_type": img.file_type,
                    "file_size": img.file_size,
                    "width": img.width,
                    "height": img.height,
                    "caption": img.caption,
                    "created_at": img.created_at.isoformat() if img.created_at else None,
                }
                for img in result.scalars().all()
            ]

    async def delete_image(self, image_id: int, user_id: int) -> bool:
        """Delete an image record and its embeddings."""
        async with async_session() as db:
            result = await db.execute(
                delete(ImageRecord).where(
                    ImageRecord.id == image_id,
                    ImageRecord.user_id == user_id,
                )
            )
            await db.commit()
            deleted = result.rowcount > 0

        if deleted:
            try:
                collection = self._get_collection()
                results = collection.get(
                    where={"image_id": str(image_id)},
                    include=[],
                )
                if results["ids"]:
                    collection.delete(ids=results["ids"])
            except Exception as e:
                logger.warning("Failed to delete image embeddings: %s", e)
        return deleted

    async def get_stats(self, user_id: int) -> dict:
        """Get image knowledge base statistics."""
        async with async_session() as db:
            result = await db.execute(
                select(ImageRecord).where(ImageRecord.user_id == user_id)
            )
            images = list(result.scalars().all())
            return {
                "total_images": len(images),
                "by_type": {},
                "total_size": sum(i.file_size for i in images),
            }

    async def ping(self) -> bool:
        """Check if the vision ChromaDB collection is accessible."""
        try:
            client = self._get_client()
            client.heartbeat()
            return True
        except Exception:
            return False


image_knowledge = ImageKnowledgeBase()
