FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
# Cloud Run tells the container which port to listen on via $PORT (default 8080)
CMD exec gunicorn --bind ":${PORT:-8080}" --workers 1 --threads 8 --timeout 0 main:app
