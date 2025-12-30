FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Copy source code
COPY src ./src

# Create necessary directories
RUN mkdir -p /reports /var/log/cyper /scans

# Expose gRPC port
EXPOSE 50051

# Run the application
CMD ["python", "-m", "cyper_brain.main"]
