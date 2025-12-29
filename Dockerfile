FROM python:3.13-slim@sha256:baf66684c5fcafbda38a54b227ee30ec41e40af1e4073edee3a7110a417756ba

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN useradd -m appuser

WORKDIR /app

COPY --chown=appuser:appuser pyproject.toml uv.lock ./

RUN uv sync --frozen --no-cache

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
