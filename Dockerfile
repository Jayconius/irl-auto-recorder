FROM python:3.11-slim

# Install FFmpeg and network tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy recorder script
COPY auto_recorder.py .

# Make script executable
RUN chmod +x auto_recorder.py

CMD ["python3", "-u", "auto_recorder.py"]
