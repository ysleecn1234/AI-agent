# Base Image: Python 3.11 Slim (Lightweight)
FROM python:3.11-slim

# Set Working Directory
WORKDIR /app

# System Dependencies (Postgres Client, Curl for Healthcheck, Libmagic for file type detection)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python Dependencies
# Copy requirements first to leverage Docker Cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Application Code
COPY . .

# Expose Port
EXPOSE 8000

# Run Application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
