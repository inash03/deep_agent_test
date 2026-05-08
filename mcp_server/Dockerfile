# syntax=docker/dockerfile:1
# Cloud Run Service B — MCP External Data Server (SSE transport)
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

# Install only what this service needs (not the full project)
RUN uv pip install --system --no-cache "mcp[cli]==1.27.0" "httpx==0.28.1"

# Copy package markers and source files required for import resolution
RUN mkdir -p src/infrastructure mcp_server
COPY src/__init__.py ./src/
COPY src/infrastructure/__init__.py ./src/infrastructure/
COPY src/infrastructure/external_data_service.py ./src/infrastructure/
COPY mcp_server/external_data_server.py ./mcp_server/

ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["python", "mcp_server/external_data_server.py"]
