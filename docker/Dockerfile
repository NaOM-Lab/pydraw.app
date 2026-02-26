# Use Python 3.12 slim image as base
# This Dockerfile supports multi-platform builds
# For local development: docker build -t your-image-name .
# For Azure deployment: docker buildx build --platform linux/amd64 -t your-image-name .
FROM python:3.12-slim

# Set build arguments for platform configuration
# TARGETPLATFORM: The platform where the image will run
# BUILDPLATFORM: The platform where the image is being built
# These are automatically set by Docker Buildx
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    graphviz \
    fonts-noto-cjk \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
# First upgrade pip to latest version
RUN pip install --no-cache-dir --upgrade pip && \
    # Install packages without the --only-binary flag to allow source builds if needed
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs tmp

# Set permissions
RUN chmod -R 755 /app

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5001

# Run the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "--timeout", "120", "app:app"] 