# 🎬 OpenIRL Auto-Recorder

Automatically records all incoming SRT streams from [OpenIRL/srtla-receiver](https://github.com/OpenIRL/srtla-receiver) with auto-discovery, segmented MKV output, and automatic cleanup.

---

## ✨ Features

- 🎬 **Auto-Recording** — records all configured SRT streams automatically in 15-minute MKV segments
- 🔍 **Auto-Discovery** — monitors OpenIRL logs and automatically adds new stream IDs
- 🧹 **Auto-Cleanup** — deletes oldest recordings when disk usage hits 85%
- 🔌 **Disconnect Protection** — 90-second grace period before stopping a recording on disconnect
- 📁 **Organised Storage** — recordings sorted by stream ID and date
- 🐳 **Docker-based** — runs anywhere Docker runs (x86 and ARM)

---

## 📋 Requirements

- [OpenIRL/srtla-receiver](https://github.com/OpenIRL/srtla-receiver) installed and running
- Docker + Docker Compose
- Ubuntu 22.04 / Debian 12 (or any Linux with Docker support)

---

## 🚀 Quick Start

### 1. Clone or download this repo

```bash
mkdir -p ~/irl-auto-recorder
cd ~/irl-auto-recorder
# Place all files here
```

### 2. Install the Auto-Recorder

```bash
chmod +x install_recorder.sh
./install_recorder.sh
```

The installer will ask:
- OpenIRL Stats host (default: `127.0.0.1:8080`)
- SRT Player port (default: `127.0.0.1:4000`)
- Segment duration (default: 15 minutes)
- Disconnect grace period (default: 90 seconds)

Just press **Enter** to accept defaults.

### 3. Add your first stream

```bash
nano ~/recordings/stream_ids.txt
```

Add one `play_` stream ID per line:
```
play_yourstream1
play_yourstream2
```

The recorder picks up changes within 30 seconds.

### 4. Verify it's working

```bash
docker logs -f irl-auto-recorder
```

Expected output:
```
[2026-03-22 12:00:00] 🚀 OpenIRL Auto-Recorder started
[2026-03-22 12:00:00] 🆕 Discovered new stream ID: play_yourstream1
```

---

## 🔍 Auto-Discovery (Recommended)

Auto-discovery monitors OpenIRL container logs and automatically adds new stream IDs to `stream_ids.txt` — no manual editing needed.

```bash
chmod +x install_discovery.sh
./install_discovery.sh
```

**How it works:**
1. Someone connects with `streamid=live_abc123`
2. Auto-discovery detects it in OpenIRL logs (within 1–2 seconds)
3. Converts `live_` → `play_` and adds to `stream_ids.txt`
4. Recorder picks it up within 30 seconds
5. Recording starts automatically

> ⚠️ Keep streaming for at least 60 seconds on first connection to ensure recording starts.

---

## 🧹 Auto-Cleanup (Recommended)

Prevents your disk from filling up by deleting the oldest recordings when usage exceeds a threshold.

```bash
chmod +x install_cleanup.sh
./install_cleanup.sh
```

The installer will ask:
- Recordings directory (default: `~/recordings`)
- Cleanup threshold (default: 85%)
- Stop cleaning at (default: 75%)
- Check interval (default: 300 seconds / 5 minutes)

---

## 📁 File Structure

```
~/irl-auto-recorder/
├── auto_recorder.py          # Main recorder script
├── Dockerfile                # Container build
├── docker-compose.yml        # Configuration
├── stream_auto_discovery.py  # Auto-discovery script
├── install_recorder.sh       # Recorder installer
├── install_discovery.sh      # Auto-discovery installer
└── install_cleanup.sh        # Auto-cleanup installer

~/recordings/
├── stream_ids.txt            # Stream ID list (add your IDs here)
├── play_stream1/
│   └── 2026-03-22/
│       ├── play_stream1_20260322_120000_part001.mkv
│       └── play_stream1_20260322_120000_part002.mkv
└── play_stream2/
    └── 2026-03-22/
        └── play_stream2_20260322_130000_part001.mkv
```

---

## ⚙️ Configuration

Edit `~/irl-auto-recorder/docker-compose.yml` to change settings:

```yaml
environment:
  - STATS_HOST=127.0.0.1:8080       # OpenIRL stats API
  - SRT_CALLER_HOST=127.0.0.1:4000  # SRT output port
  - SEGMENT_DURATION=900            # Segment length in seconds (default: 15 min)
  - DISCONNECT_GRACE=90             # Grace period before stopping (default: 90s)
  - POLL_INTERVAL=10                # Stream check interval (default: 10s)
  - DISCOVERY_INTERVAL=30           # File check interval (default: 30s)
```

After editing, restart the container:

```bash
cd ~/irl-auto-recorder
docker compose restart
```

---

## 💾 Changing Recording Location

By default recordings save to `~/recordings` on your main drive. For a dedicated SATA SSD, external USB drive, or any other mount point, follow these steps:

### Step 1 — Find your drive's mount point

```bash
lsblk -f
```

Look for your drive in the output. Common mount points:
- SATA SSD: `/mnt/ssd` or `/media/username/drivename`
- External USB: `/media/username/drivename`
- A drive you mounted manually: wherever you mounted it (e.g. `/mnt/recordings`)

If your drive isn't mounted yet, mount it first:

```bash
# Create a mount point
sudo mkdir -p /mnt/recordings

# Mount the drive (replace sdX1 with your actual device)
sudo mount /dev/sdX1 /mnt/recordings

# Verify it mounted correctly
df -h /mnt/recordings
```

### Step 2 — Make it mount automatically on boot

Find your drive's UUID:
```bash
sudo blkid /dev/sdX1
```

Add it to `/etc/fstab`:
```bash
sudo nano /etc/fstab
```

Add this line (replace UUID and filesystem type as appropriate):
```
UUID=your-uuid-here  /mnt/recordings  ext4  defaults,nofail  0  2
```

> ⚠️ The `nofail` option is important — it prevents the system failing to boot if the drive is unplugged.

### Step 3 — Set correct permissions

```bash
sudo chown -R $USER:$USER /mnt/recordings
```

### Step 4 — Update docker-compose.yml

Edit `~/irl-auto-recorder/docker-compose.yml` and change the volume mount:

```yaml
volumes:
  - /mnt/recordings:/root/recordings  # Change to your mount point
```

Also update the environment variable:

```yaml
environment:
  - RECORDINGS_BASE=/root/recordings  # Keep this as-is, it's inside the container
```

### Step 5 — Move existing recordings (optional)

If you want to keep your existing recordings:

```bash
mv ~/recordings/* /mnt/recordings/
```

### Step 6 — Restart the recorder

```bash
cd ~/irl-auto-recorder
docker compose down
docker compose up -d --build
```

### Step 7 — Verify recordings are going to the new location

```bash
docker logs -f irl-auto-recorder
ls -lh /mnt/recordings/
```

---

### 💡 Tips for Storage Drives

| Drive Type | Recommended Filesystem | Notes |
|---|---|---|
| SATA SSD | ext4 | Best for Linux, reliable for sustained writes |
| External USB SSD | ext4 | Format on Linux for best performance |
| External USB (Windows shared) | exFAT | Use if drive is shared between Windows and Linux |
| NAS / Network share | — | Mount via NFS or SMB, then follow steps above |

> ⚠️ Avoid FAT32 — it has a 4GB file size limit which will cause recording failures on long streams.

---

## 📊 Useful Commands

```bash
# Recorder
docker logs -f irl-auto-recorder                   # Live logs
cd ~/irl-auto-recorder && docker compose restart   # Restart recorder
nano ~/recordings/stream_ids.txt                   # Edit stream list

# Auto-Discovery
sudo journalctl -u openirl-discovery -f            # Live logs
sudo systemctl restart openirl-discovery           # Restart
sudo systemctl status openirl-discovery            # Check status

# Auto-Cleanup
sudo journalctl -u openirl-cleanup -f              # Live logs
sudo systemctl restart openirl-cleanup             # Restart

# Storage
df -h /                                            # Check disk space
du -sh ~/recordings                                # Total recording size
find ~/recordings -name "*.mkv" | wc -l            # Count recordings
```

---

## 🔍 Troubleshooting

### Recorder not starting
```bash
docker logs irl-auto-recorder
docker ps -a | grep irl-auto-recorder

# Rebuild if needed
cd ~/irl-auto-recorder
docker compose down
docker compose up -d --build
```

### Auto-discovery not adding streams
```bash
sudo systemctl status openirl-discovery
sudo journalctl -u openirl-discovery -f
sudo systemctl restart openirl-discovery
```

### Stream not recording
```bash
# Check stream ID is in the list
cat ~/recordings/stream_ids.txt

# Check stream is active via stats API
curl http://127.0.0.1:8080/stats/play_YOURSTREAMID

# Check recorder logs
docker logs --tail 50 irl-auto-recorder
```

---

## 📝 Notes

- Only `play_` stream IDs are recorded. Auto-discovery converts `live_` → `play_` automatically.
- MKV format is used for crash-safe recording — completed segments are always intact even if the system crashes mid-stream.
- The recorder and auto-discovery use the same `stream_ids.txt` file — you can mix manual and auto-discovered entries freely.

---

## 🙏 Credits

Built on top of:
- [OpenIRL/srtla-receiver](https://github.com/OpenIRL/srtla-receiver)
- [OpenIRL/srtla](https://github.com/OpenIRL/srtla)
- [OpenIRL/srt-live-server](https://github.com/OpenIRL/srt-live-server)
