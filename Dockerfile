FROM python:3.13-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY auto_recorder.py .

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python3", "/app/auto_recorder.py", "healthcheck"]

CMD ["python3", "-u", "/app/auto_recorder.py"]
