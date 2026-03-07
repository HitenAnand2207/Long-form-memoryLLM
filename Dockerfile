# ─── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies in a separate layer for better layer caching
COPY requirements-minimal.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements-minimal.txt

# Optionally install FAISS + sentence-transformers (comment out if not needed)
# RUN pip install --no-cache-dir --prefix=/install faiss-cpu sentence-transformers

# ─── Runtime stage ────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /install /usr/local

# Copy source code
COPY src/ ./src/
COPY web_interface.html ./
COPY diagnose.py ./

# Create the data directory (mounted as a volume in production)
RUN mkdir -p /app/data/embeddings

# Expose Flask API port
EXPOSE 5000

# Environment defaults (override with docker run -e)
ENV FLASK_ENV=production \
    MEMORY_DB_PATH=/app/data/memories.db \
    MEMORY_AGENT_VERBOSE=false

# Health check — mirrors the /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

# Default: start the REST API server
CMD ["python", "-m", "src.api_server"]
