from sqlalchemy import Column, Integer, String, DateTime, func
from backend.database.base import Base


class ImageRecord(Base):
    """Track uploaded images for vision processing."""

    __tablename__ = "images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    stored_name = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_size = Column(Integer, nullable=False)
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    caption = Column(String(2000), nullable=True)
    ocr_text = Column(String(10000), nullable=True)
    description = Column(String(2000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
