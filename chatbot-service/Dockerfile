FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8002

# Railway injects $PORT; default to 8002 locally. WEB_CONCURRENCY tunes the
# async worker count (the chat path is I/O-bound, so a few workers go far).
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8002} --workers ${WEB_CONCURRENCY:-2}"]
