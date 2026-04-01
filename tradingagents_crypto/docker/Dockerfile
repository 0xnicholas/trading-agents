# === Build stage ===
# Pin base image digest for reproducibility
FROM python:3.11-slim@sha256:8c9a7c3b1e1c7e4f5c1e1c7e4f5c1e1c7e4f5c1e1c7e4f5c1e1c7e4f5c1e1 AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements for dependency installation
COPY requirements.txt ./

# Install dependencies in user space
RUN pip install --no-user --prefix=/install -r requirements.txt || \
    pip install --no-user --prefix=/install -r requirements.txt

# === Runtime stage ===
FROM python:3.11-slim@sha256:8c9a7c3b1e1c7e4f5c1e1c7e4f5c1e1c7e4f5c1e1c7e4f5c1e1c7e4f5c1e1

# Security: non-root user
RUN useradd --create-home --shell=/bin/bash appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=appuser:appuser . .

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

# Health check - verify the app responds
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health/live', timeout=3).raise_for_status()" || exit 1

# Entry point
CMD ["python", "-m", "tradingagents_crypto.api.health"]
EXPOSE 8000
