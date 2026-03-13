# Use official lightweight Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and template
COPY main.py .
COPY template.docx .

# Cloud Run expects the app to listen on $PORT (default 8080)
ENV PORT=8080

# Use gunicorn for production
CMD exec gunicorn --bind "0.0.0.0:$PORT" --workers 2 --threads 4 --timeout 60 main:app
