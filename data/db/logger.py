"""Helper utility to save query logs into database query_logs table."""

from typing import List, Optional
from sqlalchemy.orm import Session
from data.db.models import QueryLog


def log_query(
    db: Session,
    query: str,
    answer: str,
    cited_chunk_ids: List[str],
    verified: bool = False,
    state: Optional[str] = None,
) -> QueryLog:
    """Save a query execution record to the query_logs table.

    Args:
        db: SQLAlchemy DB Session
        query: User input query
        answer: Generated answer text
        cited_chunk_ids: List of chunk_ids cited in the answer
        verified: Citation verification status flag
        state: State/jurisdiction parameter if provided

    Returns:
        QueryLog: Created database log record
    """
    log_entry = QueryLog(
        query=query,
        state=state,
        answer=answer,
        cited_chunk_ids=cited_chunk_ids,
        verified=verified,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry
