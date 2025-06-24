# Use official Python base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies for mysqlclient and build tools
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libmariadb-dev \
    libmariadb-dev-compat \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .

# Set up virtual environment and install deps
RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && pip install --upgrade pip \
    && pip install -r requirements.txt

# Add virtualenv to PATH
ENV PATH="/opt/venv/bin:$PATH"

# Copy the rest of the app
COPY . .

# Download the spaCy model (in case it isn't in the .whl already)
RUN python -m spacy download en_core_web_sm

# Default start command using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
