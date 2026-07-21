import logging
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.session import async_session
from backend.models.document import Document

logger = logging.getLogger(__name__)


class DocumentService:
    """CRUD operations for document metadata in SQLite."""

    async def create(
        self,
        user_id: int,
        filename: str,
        file_type: str,
        file_size: int,
        status: str = "processing",
    ) -> Document:
        """Create a new document record."""
        async with async_session() as db:
            doc = Document(
                user_id=user_id,
                filename=filename,
                file_type=file_type,
                file_size=file_size,
                status=status,
            )
            db.add(doc)
            await db.commit()
            await db.refresh(doc)
            logger.info("Document created: id=%d filename=%s", doc.id, filename)
            return doc

    async def update_status(
        self,
        doc_id: int,
        status: str,
        chunk_count: int = 0,
        error_message: Optional[str] = None,
    ) -> Optional[Document]:
        """Update document processing status."""
        async with async_session() as db:
            result = await db.execute(
                select(Document).where(Document.id == doc_id)
            )
            doc = result.scalar_one_or_none()
            if not doc:
                return None
            doc.status = status
            doc.chunk_count = chunk_count
            if error_message:
                doc.error_message = error_message
            await db.commit()
            await db.refresh(doc)
            return doc

    async def get(self, doc_id: int, user_id: int) -> Optional[Document]:
        """Get a document by ID (with ownership check)."""
        async with async_session() as db:
            result = await db.execute(
                select(Document).where(
                    Document.id == doc_id,
                    Document.user_id == user_id,
                )
            )
            return result.scalar_one_or_none()

    async def list_user_documents(self, user_id: int) -> list[Document]:
        """List all documents for a user."""
        async with async_session() as db:
            result = await db.execute(
                select(Document)
                .where(Document.user_id == user_id)
                .order_by(Document.created_at.desc())
            )
            return list(result.scalars().all())

    async def delete(self, doc_id: int, user_id: int) -> bool:
        """Delete a document record (with ownership check)."""
        async with async_session() as db:
            result = await db.execute(
                delete(Document).where(
                    Document.id == doc_id,
                    Document.user_id == user_id,
                )
            )
            await db.commit()
            deleted = result.rowcount > 0
            if deleted:
                logger.info("Document deleted: id=%d", doc_id)
            return deleted

    async def get_user_stats(self, user_id: int) -> dict:
        """Get document statistics for a user."""
        async with async_session() as db:
            result = await db.execute(
                select(Document).where(Document.user_id == user_id)
            )
            docs = list(result.scalars().all())
            total = len(docs)
            total_chunks = sum(d.chunk_count for d in docs)
            by_type = {}
            for d in docs:
                by_type[d.file_type] = by_type.get(d.file_type, 0) + 1
            return {
                "total_documents": total,
                "total_chunks": total_chunks,
                "by_type": by_type,
            }


document_service = DocumentService()
