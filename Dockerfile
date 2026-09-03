FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY . /app

# Set environment variables
ENV PORT=8090
ENV PYTHONUNBUFFERED=1

EXPOSE 8090

CMD ["python", "app.py"]
