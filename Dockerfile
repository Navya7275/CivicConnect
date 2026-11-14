# Multi-stage Dockerfile for CivicConnect Backend
FROM python:3.12-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and data assets
COPY backend/ ./backend/
COPY data/ ./data/

# Initialize SQLite fallback database, load statutory seeds, and compile search indexes
ENV DATABASE_URL=sqlite:///./civicconnect.db
ENV PYTHONPATH=/app
RUN python -m data.db.database && \
    python -m data.ingestion.load_seed && \
    python -m data.ingestion.load_welfare && \
    python -m data.indexing.build_index

# Expose backend port
EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start FastAPI server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
