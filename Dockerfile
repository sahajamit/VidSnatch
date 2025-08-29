# Multi-stage Dockerfile for VidSnatch - supports both webapp and MCP server modes
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir 'mcp>=1.12.0,<2.0.0'

# Copy application code
COPY src/ ./src/
COPY static/ ./static/
COPY web_app.py mcp_server.py mcp_config.json ./

# Create downloads directory
RUN mkdir -p /app/downloads

# Expose ports (8080 for webapp, 3000 for MCP stdio)
EXPOSE 8080

# Create entrypoint script
RUN echo '#!/bin/bash\n\
if [ "$1" = "webapp" ]; then\n\
    exec uvicorn web_app:app --host 0.0.0.0 --port 8080\n\
elif [ "$1" = "mcp" ]; then\n\
    exec python3 mcp_server.py\n\
else\n\
    echo "Usage: docker run <image> [webapp|mcp]"\n\
    echo "  webapp - Start web application on port 8080"\n\
    echo "  mcp    - Start MCP server for AI assistants"\n\
    exit 1\n\
fi' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Default to webapp mode
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["webapp"]
