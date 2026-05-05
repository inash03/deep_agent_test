# syntax=docker/dockerfile:1
# Cloud Run Service B — MCP External Data Server (SSE transport)
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
RUN uv pip install --system --no-cache "."

COPY src/infrastructure/external_data_service.py ./src/infrastructure/
COPY mcp_server/external_data_server.py ./mcp_server/

ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["python", "mcp_server/external_data_server.py"]
