FROM python:3.12-slim AS base

WORKDIR /app

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Install runtime dependencies (non-editable — no .egg-link needed in container)
COPY pyproject.toml ./
# [gcp] extra を含めてインストール: SECRET_BACKEND=gcp で GCP Secret Manager を使う場合に必要
# SECRET_BACKEND=env (デフォルト) の場合も無害（インポートされないだけ）
RUN uv pip install --system --no-cache ".[gcp]"

# Copy application source
COPY src/ ./src/

# --- production stage ---
FROM base AS production

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# --- test stage ---
FROM base AS test

# Install dev dependencies (pytest, httpx, ruff, mypy)
RUN uv pip install --system --no-cache ".[dev]"

COPY tests/ ./tests/

CMD ["pytest", "--tb=short", "-v"]
