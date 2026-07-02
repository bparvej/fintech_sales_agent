# ============================================================
# Dockerfile — FinTech Sales Intelligence
# ============================================================
# Multi-stage build for production-ready Python application.
# ============================================================

# ---- Stage 1: Builder ----
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install .

# ---- Stage 2: Runtime ----
FROM python:3.12-slim AS runtime

LABEL maintainer="FinTech Sales Intelligence Team"
LABEL description="AI-powered Sales Intelligence Platform"

# System dependencies for Playwright & crawling
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

WORKDIR /app

# Install Playwright browsers
RUN playwright install chromium

COPY . .

# Non-root user for security
RUN groupadd -r fintech && useradd -r -g fintech fintech \
    && chown -R fintech:fintech /app
USER fintech

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.presentation.api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
