FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv sync --frozen --no-dev

RUN useradd --create-home --uid 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD [".venv/bin/uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
