from sqlalchemy import Column, Integer, String, DateTime, func
from backend.database.base import Base


class Document(Base):
    """Track uploaded documents for RAG."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_size = Column(Integer, nullable=False)
    chunk_count = Column(Integer, default=0)
    status = Column(String(20), default="processing")
    error_message = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
