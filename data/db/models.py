"""SQLAlchemy models for CivicConnect database.

Defines tables:
1. documents - source acts and scheme documents
2. chunks - searchable statutory/welfare text chunks with metadata
3. query_logs - system query execution and citation verification logs
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models."""
    pass


class Document(Base):
    """Represents an overarching document (Act, Scheme, etc.)."""
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., 'India Code', 'MyScheme'
    jurisdiction: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., 'Central', 'Madhya Pradesh'
    source_url: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    chunks: Mapped[List["Chunk"]] = relationship(
        "Chunk", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document(id='{self.id}', title='{self.title}', jurisdiction='{self.jurisdiction}')>"


class Chunk(Base):
    """Represents a searchable chunk corresponding to a section or scheme detail."""
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chunk_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    document_id: Mapped[str] = mapped_column(String(100), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    
    text: Mapped[str] = mapped_column(Text, nullable=False)
    act: Mapped[str] = mapped_column(String(255), nullable=False)
    chapter: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    section: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    jurisdiction: Mapped[str] = mapped_column(String(100), nullable=False)
    effective_date: Mapped[str] = mapped_column(String(20), nullable=False)  # YYYY-MM-DD
    source_url: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")

    def to_dict(self) -> dict:
        """Convert model instance to the standard chunk contract dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "act": self.act,
            "chapter": self.chapter,
            "section": self.section,
            "jurisdiction": self.jurisdiction,
            "effective_date": self.effective_date,
            "source_url": self.source_url,
        }

    def __repr__(self) -> str:
        return f"<Chunk(chunk_id='{self.chunk_id}', act='{self.act}', section='{self.section}')>"


class QueryLog(Base):
    """Represents a log entry for a user query and system answer."""
    __tablename__ = "query_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    cited_chunk_ids: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<QueryLog(id={self.id}, query='{self.query[:30]}...', verified={self.verified})>"
