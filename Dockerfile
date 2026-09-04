FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . /app

# Set environment variables
ENV PYTHONUNBUFFERED=1

EXPOSE 10000

CMD ["sh", "-c", "gunicorn wsgi:app --bind 0.0.0.0:${PORT:-10000} --workers 2 --threads 4 --timeout 120"]
