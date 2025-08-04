# Dockerfile for Resume Matcher

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download SPAcy model
RUN python -m spacy download en_core_web_sm || echo "spaCy model download failed, will use NLTK fallback"

# Copy source and main files
COPY src/ ./src/
COPY main.py .
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p data/sample_resumes data/job_descriptions data/output logs

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "main.py", "--help"]
