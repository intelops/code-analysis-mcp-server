# Use Python 3.12.8-slim as the base image
FROM python:3.12.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PROJECT_PATH="/project"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && curl -LO https://github.com/ast-grep/ast-grep/releases/latest/download/ast-grep-linux-x64.tar.gz \
    && tar -xzf ast-grep-linux-x64.tar.gz \
    && mv sg /usr/local/bin/ast-grep \
    && chmod +x /usr/local/bin/ast-grep \
    && rm ast-grep-linux-x64.tar.gz \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a directory for the project mount
RUN mkdir -p /project

# Set working directory
WORKDIR /app

# Clone the repository (replace with your actual repository URL)
RUN git clone https://github.com/yourusername/code-analysis-mcp-server.git . \
    && pip install --no-cache-dir -e .

# Expose the port for the MCP server
EXPOSE 8000

# Create a volume for the project
VOLUME ["/project"]

# Command to run the server
ENTRYPOINT ["code-analysis-server"]
