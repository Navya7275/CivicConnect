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
    effective_date: Mapped[str] = mapped_column(String(20), nullable=False)  # YYYY-MM-DD (Commencement date)
    assent_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default=None)  # YYYY-MM-DD (Presidential assent)
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)  # Quoted text snippet for precise citation
    source_url: Mapped[str] = mapped_column(Text, nullable=False)

    # Where a reader can actually open this law today.
    #
    # Deliberately separate from source_url, which records where the text was
    # fetched from and is what raw_sha256 is the hash of. The two are not always
    # the same page: India Code serves whole Acts at a handle URL, and those
    # handle pages now fail with a CDN error, so every citation in the product
    # was a dead end for users.
    #
    # Overwriting source_url with a working link would have made raw_sha256 the
    # hash of a page we no longer point at -- the same incoherence #22 resolved.
    # So source_url keeps its provenance meaning and this carries the link the
    # UI offers. Null means there is no better link and the UI falls back to
    # source_url.
    reference_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)

    # Cryptographic Provenance Metadata (Issue #5)
    raw_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, default=None)
    text_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, default=None)
    fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    extraction_method: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default="manual")  # html, pdf, api, manual
    reviewer_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default=None)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")

    def to_dict(self) -> dict:
        """Convert model instance to the standard chunk contract dictionary with provenance."""
        res = {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "act": self.act,
            "chapter": self.chapter,
            "section": self.section,
            "jurisdiction": self.jurisdiction,
            "effective_date": self.effective_date,
            "source_url": self.source_url,
        }
        if self.reference_url:
            res["reference_url"] = self.reference_url
        if self.assent_date:
            res["assent_date"] = self.assent_date
        if self.excerpt:
            res["excerpt"] = self.excerpt
        if self.raw_sha256:
            res["raw_sha256"] = self.raw_sha256
        if self.text_sha256:
            res["text_sha256"] = self.text_sha256
        if self.fetched_at:
            res["fetched_at"] = self.fetched_at.isoformat()
        if self.extraction_method:
            res["extraction_method"] = self.extraction_method
        if self.reviewer_name:
            res["reviewer_name"] = self.reviewer_name
        return res

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
