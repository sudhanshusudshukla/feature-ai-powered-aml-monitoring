# Backend Dockerfile for AML Transaction Monitoring Platform
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
# Use ARG to allow optional postgres dependencies
ARG INSTALL_SPEC=.
RUN pip install --no-cache-dir "$INSTALL_SPEC"

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Copy entrypoint script
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# Expose port
EXPOSE 8000

# Run entrypoint script that handles migrations and seeding
ENTRYPOINT ["./docker-entrypoint.sh"]

# Start uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
