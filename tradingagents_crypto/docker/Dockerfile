# === Build stage ===
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements for dependency installation
COPY pyproject.toml ./

# Install dependencies in user space
RUN pip install --no-user --prefix=/install -r /dev/null 2>/dev/null || \
    pip install --no-user --prefix=/install .

# === Runtime stage ===
FROM python:3.11-slim

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

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health/live').raise_for_status()" || exit 1

# Entry point
CMD ["python", "-m", "tradingagents_crypto.api.health"]
EXPOSE 8000
