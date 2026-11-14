from data.db.database import SessionLocal
from data.db.models import Chunk


def load_chunks_from_database():
    """
    Load all searchable chunks from the CivicConnect database.

    Returns:
        list[dict]: Chunks using the standard retrieval chunk contract.
    """

    db = SessionLocal()

    try:
        chunks = (
            db.query(Chunk)
            .order_by(Chunk.id)
            .all()
        )

        return [
            chunk.to_dict()
            for chunk in chunks
        ]

    finally:
        db.close()