
# 🛠️ Manual Installation

> 💡 **Just want to get started?** Use [QUICKSTART.md](QUICKSTART.md) — it handles all of this automatically via the installer scripts.

The following is for advanced users who want to understand what the installers do, run components manually, or integrate this into an existing setup.

---

## Prerequisites

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # Add your user to the docker group
newgrp docker                   # Apply group change without logout
```

---

## Recorder Container

The recorder runs as a Docker container built from the included `Dockerfile`. To build and start it manually without the installer:

```bash
cd ~/irl-auto-recorder

# Create recordings directory and stream list
mkdir -p ~/recordings
touch ~/recordings/stream_ids.txt

# Build and start
docker compose up -d --build

# Verify
docker ps | grep irl-auto-recorder
docker logs -f irl-auto-recorder
```

To run without Docker Compose directly:
```bash
docker build -t irl-auto-recorder .
docker run -d \
  --name irl-auto-recorder \
  --network host \
  --restart unless-stopped \
  -v ~/recordings:/root/recordings \
  -e STATS_HOST=127.0.0.1:8080 \
  -e SRT_CALLER_HOST=127.0.0.1:4000 \
  -e SEGMENT_DURATION=900 \
  -e DISCONNECT_GRACE=90 \
  irl-auto-recorder
```

---

## Auto-Discovery Service

The auto-discovery script runs as a systemd service. To install it manually:

```bash
# Copy script
cp stream_auto_discovery.py ~/stream_auto_discovery.py
chmod +x ~/stream_auto_discovery.py

# Install systemd service (replace 'youruser' with your Linux username)
sudo cp openirl-discovery.service /etc/systemd/system/
sudo sed -i 's/%i/youruser/g' /etc/systemd/system/openirl-discovery.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable openirl-discovery
sudo systemctl start openirl-discovery

# Verify
sudo systemctl status openirl-discovery
```

---

## Auto-Cleanup Service

The cleanup script is a bash script run by a systemd service. To install manually:

```bash
# Copy and make executable
cp auto_cleanup.sh ~/auto_cleanup.sh
chmod +x ~/auto_cleanup.sh

# Install systemd service
sudo cp openirl-cleanup.service /etc/systemd/system/
sudo sed -i 's/%i/youruser/g' /etc/systemd/system/openirl-cleanup.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable openirl-cleanup
sudo systemctl start openirl-cleanup
```

---

## Running Without Docker

If you prefer to run `auto_recorder.py` directly on the host rather than in Docker, ensure FFmpeg is installed:

```bash
sudo apt install ffmpeg python3 -y
python3 ~/irl-auto-recorder/auto_recorder.py
```

Or as a systemd service for auto-start on boot:

```bash
sudo nano /etc/systemd/system/irl-recorder.service
```

```ini
[Unit]
Description=IRL Auto-Recorder
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser
Environment=STATS_HOST=127.0.0.1:8080
Environment=SRT_CALLER_HOST=127.0.0.1:4000
Environment=SEGMENT_DURATION=900
Environment=DISCONNECT_GRACE=90
Environment=RECORDINGS_BASE=/home/youruser/recordings
ExecStart=/usr/bin/python3 /home/youruser/irl-auto-recorder/auto_recorder.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable irl-recorder
sudo systemctl start irl-recorder
```
