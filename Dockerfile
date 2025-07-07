# Multi-stage build for PDF2UBL

# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY src/pdf2ubl/gui/frontend/package*.json ./
RUN npm ci --only=production
COPY src/pdf2ubl/gui/frontend/ ./
RUN npm run build

# Stage 2: Python application
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-nld \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY templates/ ./templates/
COPY pdf2ubl.py .
COPY *.py ./

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/build ./src/pdf2ubl/gui/frontend/build

# Create non-root user
RUN useradd -m -u 1000 pdf2ubl && chown -R pdf2ubl:pdf2ubl /app
USER pdf2ubl

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:8000/api/health || exit 1

# Run the application (listen on all interfaces for container access)
CMD ["python3", "-m", "src.pdf2ubl.cli", "gui", "--host", "0.0.0.0", "--port", "8000"]