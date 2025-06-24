# Use a minimal Python base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy all files into the container
COPY . /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc libmysqlclient-dev default-libmysqlclient-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expose port for gunicorn
EXPOSE 8000

# Run the app using Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]
