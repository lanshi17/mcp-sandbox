FROM python:3.12-slim

WORKDIR /app

# Install basic tools
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Create non-root user
RUN groupadd -r python && useradd -r -g python -d /home/python -m python

# Provide directory for additional packages installation
RUN mkdir -p /app/results && chown -R python:python /app

# Set secure execution user
USER python

# Set working directory to results directory
WORKDIR /app/results

# Container entry point - use sleep infinity to keep container running
CMD ["sleep", "infinity"] 