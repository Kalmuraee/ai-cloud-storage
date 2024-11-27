# Base stage for shared dependencies
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create logs directory and set permissions
RUN mkdir -p /app/logs \
    && chown -R nobody:nogroup /app/logs \
    && chmod 777 /app/logs

# Copy requirements
COPY requirements.txt .

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir \
        debugpy \
        black \
        flake8 \
        isort

# Copy project files
COPY . .

# Production stage
FROM base as production

# Install production dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
