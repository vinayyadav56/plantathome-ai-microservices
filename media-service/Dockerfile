FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libglib2.0-0 libsm6 libxext6 libxrender-dev ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download rembg background removal model
RUN python -c "from rembg import new_session; new_session('u2net')"

COPY . .

EXPOSE 8007

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007"]
