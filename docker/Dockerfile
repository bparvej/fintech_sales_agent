# ============================================================
# Dockerfile — FinTech Sales Intelligence
# ============================================================

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
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

# Copy project
COPY . .

# Upgrade pip
RUN pip install --upgrade pip

# Install application
RUN pip install .

# Install Playwright browser
RUN playwright install chromium

# Create non-root user
RUN groupadd -r fintech && \
    useradd -r -g fintech fintech && \
    chown -R fintech:fintech /app

USER fintech

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
CMD curl -f http://localhost:${PORT:-8000}/api/v1/health || exit 1

CMD ["sh","-c","uvicorn app.presentation.api.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}"]