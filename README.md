# 🎬 OpenIRL Auto-Recorder

Automatically records all incoming SRT streams from [OpenIRL/srtla-receiver](https://github.com/OpenIRL/srtla-receiver) with auto-discovery, segmented MKV output, and automatic cleanup.

## ✨ Features

- 🎬 **Auto-Recording** — records all active SRT streams in crash-safe 15-minute MKV segments
- 🔍 **Auto-Discovery** — monitors OpenIRL logs and automatically adds new stream IDs without any manual input
- 🧹 **Auto-Cleanup** — deletes the oldest recordings when disk usage hits a configurable threshold
- 🔌 **Disconnect Protection** — a configurable grace period prevents recordings from stopping on brief network drops
- 📁 **Organised Storage** — recordings are automatically sorted by stream ID and date
- 🐳 **Docker-based** — works on any Linux system running Docker, including x86 and ARM (Raspberry Pi)

---

## 📋 Requirements

- [OpenIRL/srtla-receiver](https://github.com/OpenIRL/srtla-receiver) installed and running
- Docker + Docker Compose
- Ubuntu 22.04 / Debian 12 or any Linux distribution with Docker support

---

## 📦 Components

### Auto-Recorder (`auto_recorder.py`)
The core component. Polls the OpenIRL stats API every 10 seconds to check which streams are active, then launches an FFmpeg process per stream writing segmented MKV files. If a stream goes offline it waits for the grace period to expire before stopping the recording — protecting against brief disconnections.

### Auto-Discovery (`stream_auto_discovery.py`)
An optional systemd service that monitors the OpenIRL Docker container logs in real time. When it detects a new `live_` stream ID connecting, it automatically converts it to the equivalent `play_` ID and appends it to `stream_ids.txt`. The recorder picks it up within 30 seconds.

### Auto-Cleanup (`auto_cleanup.sh`)
An optional systemd service that checks disk usage on a configurable interval. When usage exceeds the threshold (default 85%) it deletes the oldest recording segments until usage drops below the target level (default 75%).

---

## ⚙️ Configuration

All settings are configured via environment variables in `~/irl-auto-recorder/docker-compose.yml`:

| Variable | Default | Description |
|---|---|---|
| `STATS_HOST` | `127.0.0.1:8080` | OpenIRL stats API host and port |
| `SRT_CALLER_HOST` | `127.0.0.1:4000` | SRT output port to record from |
| `SEGMENT_DURATION` | `900` | Recording segment length in seconds (default 15 min) |
| `DISCONNECT_GRACE` | `90` | Seconds to wait before stopping after a disconnect |
| `POLL_INTERVAL` | `10` | How often to check active streams in seconds |
| `DISCOVERY_INTERVAL` | `30` | How often to check `stream_ids.txt` for new entries |
| `RECORDINGS_BASE` | `/root/recordings` | Recording output path inside the container |

After editing, apply changes with:
```bash
cd ~/irl-auto-recorder && docker compose restart
```

---

## ⚡ Quick & Easy Install

> [!TIP]
> ### 🟢 New to this? Start here.
> The **[QUICKSTART.md](QUICKSTART.md)** guide walks you through the entire setup from start to finish with simple copy-paste commands — no Linux expertise required.
>
> Just clone the repo, run the installer, and you're recording in minutes.
>
> **➡️ [Open the Quick Start Guide →](QUICKSTART.md)**

---

## 🛠️ Manual Installation

> [!NOTE]
> For advanced users who want to run components manually, understand what the installers do, or integrate this into an existing setup.
>
> **➡️ [Open the Manual Installation Guide →](INSTALL.md)**

---

<details>
<summary>💾 Recording Location</summary>

## 💾 Recording Location

By default recordings are saved to `~/recordings`. To use a dedicated drive such as a SATA SSD, M.2 drive, or external USB:

**1. Find and mount your drive:**
```bash
lsblk -f
sudo mkdir -p /mnt/recordings
sudo mount /dev/sdX1 /mnt/recordings
```

**2. Make the mount permanent via `/etc/fstab`:**
```bash
sudo blkid /dev/sdX1        # Get UUID
sudo nano /etc/fstab
```
Add:
```
UUID=your-uuid-here  /mnt/recordings  ext4  defaults,nofail  0  2
```
> The `nofail` flag prevents boot failure if the drive is unplugged.

**3. Set permissions:**
```bash
sudo chown -R $USER:$USER /mnt/recordings
```

**4. Update `docker-compose.yml`:**
```yaml
volumes:
  - /mnt/recordings:/root/recordings
```

**5. Restart the recorder:**
```bash
cd ~/irl-auto-recorder
docker compose down && docker compose up -d --build
```

### Filesystem Recommendations

| Drive Type | Filesystem | Notes |
|---|---|---|
| SATA / M.2 SSD | ext4 | Best performance on Linux |
| External USB SSD | ext4 | Format on Linux for best results |
| Shared with Windows | exFAT | Use only if the drive is also used on Windows |
| NAS / Network share | — | Mount via NFS or SMB first, then follow steps above |

> ⚠️ **Avoid FAT32** — its 4GB file size limit will cause recording failures on long streams.

</details>

---

<details>
<summary>📁 File Structure</summary>

## 📁 File Structure

```
~/irl-auto-recorder/
├── auto_recorder.py          # Main recorder — polls stats API and manages FFmpeg
├── stream_auto_discovery.py  # Auto-discovery — monitors OpenIRL logs
├── Dockerfile                # Container definition
├── docker-compose.yml        # Environment config and volume mounts
├── install_recorder.sh       # Interactive installer for the recorder
├── install_discovery.sh      # Installer for auto-discovery systemd service
├── install_cleanup.sh        # Installer for auto-cleanup systemd service
└── openirl-discovery.service # systemd unit file for auto-discovery

~/recordings/
├── stream_ids.txt            # List of play_ IDs to record (one per line)
├── play_stream1/
│   └── 2026-03-22/
│       ├── play_stream1_20260322_120000_part001.mkv
│       └── play_stream1_20260322_120000_part002.mkv
└── play_stream2/
    └── 2026-03-22/
        └── play_stream2_20260322_130000_part001.mkv
```

</details>

---

<details>
<summary>🔧 Managing Streams</summary>

## 🔧 Managing Streams

If auto-discovery is installed, new streams are added to `stream_ids.txt` automatically within 30 seconds of a publisher connecting. If you need to add a stream manually — for example before a publisher connects, or if auto-discovery isn't installed — add the `play_` stream ID directly:

**Manually add a stream:**
```bash
echo "play_yourstreamid" >> ~/recordings/stream_ids.txt
```

The recorder checks `stream_ids.txt` every 30 seconds and will start recording automatically once the stream is both listed and active.

**Remove a stream from the list:**
```bash
nano ~/recordings/stream_ids.txt
# Delete the relevant play_ line, save with Ctrl+O, Ctrl+X
```

**View active stream stats:**
```bash
curl http://127.0.0.1:8080/stats/play_YOURSTREAMID
```

**View today's recordings:**
```bash
ls -lh ~/recordings/*/$(date +%Y-%m-%d)/
```

</details>

---

<details>
<summary>📂 Viewing & Downloading Recordings</summary>

## 📂 Viewing & Downloading Recordings

[File Browser](https://github.com/filebrowser/filebrowser) is a lightweight web-based file manager that makes it easy to browse, download, and manage your recordings from any device on your network — no command line needed.

**Install File Browser:**
```bash
curl -fsSL https://raw.githubusercontent.com/filebrowser/get/master/get.sh | bash
```

**Run pointing at your recordings folder:**
```bash
filebrowser -r ~/recordings -a 0.0.0.0 -p 8082
```

**Access it in your browser:**
```
http://YOUR-SERVER-IP:8082
```

Default login is `admin` / `admin` — change this immediately:
```bash
filebrowser -r ~/recordings config set --username admin
filebrowser -r ~/recordings users update admin --password yournewpassword
```

**Run File Browser as a systemd service (auto-starts on boot):**
```bash
sudo nano /etc/systemd/system/filebrowser.service
```

```ini
[Unit]
Description=File Browser
After=network.target

[Service]
Type=simple
User=youruser
ExecStart=/usr/local/bin/filebrowser -r /home/youruser/recordings -a 0.0.0.0 -p 8082
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable filebrowser
sudo systemctl start filebrowser
```

> 💡 If you're using Tailscale, File Browser is only accessible on your Tailscale network — no need to expose port 8082 publicly.

</details>

---

<details>
<summary>📊 Service Management</summary>

## 📊 Service Management

```bash
# Recorder (Docker)
docker ps | grep irl-auto-recorder                 # Check running
docker logs -f irl-auto-recorder                   # Live logs
cd ~/irl-auto-recorder && docker compose restart   # Restart
docker compose down && docker compose up -d        # Full restart

# Auto-Discovery (systemd)
sudo systemctl status openirl-discovery            # Check status
sudo systemctl restart openirl-discovery           # Restart
sudo journalctl -u openirl-discovery -f            # Live logs

# Auto-Cleanup (systemd)
sudo systemctl status openirl-cleanup              # Check status
sudo systemctl restart openirl-cleanup             # Restart
sudo journalctl -u openirl-cleanup -f              # Live logs

# Disk
df -h /                                            # Check disk space
du -sh ~/recordings                                # Total recording size
find ~/recordings -name "*.mkv" | wc -l            # Count MKV files
```

</details>

---

<details>
<summary>🔍 Troubleshooting</summary>

## 🔍 Troubleshooting

### Recorder container not starting
```bash
docker logs irl-auto-recorder
# If needed, rebuild:
cd ~/irl-auto-recorder && docker compose down && docker compose up -d --build
```

### Streams not being recorded
1. Confirm the stream ID is in `stream_ids.txt`: `cat ~/recordings/stream_ids.txt`
2. Confirm the stream is active: `curl http://127.0.0.1:8080/stats/play_YOURSTREAMID`
3. Check recorder logs: `docker logs --tail 50 irl-auto-recorder`

### Auto-discovery not detecting new streams
1. Check the service is running: `sudo systemctl status openirl-discovery`
2. Check OpenIRL logs directly: `docker logs srtla-receiver | grep streamid`
3. If no `streamid=` entries appear in logs, auto-discovery won't trigger — add IDs manually to `stream_ids.txt` instead

### Disk filling up
- Lower the cleanup threshold in the auto-cleanup installer (e.g. 75% instead of 85%)
- Or point recordings at a larger dedicated drive — see [Recording Location](#-recording-location)

</details>

---

<details>
<summary>📝 Notes</summary>

## 📝 Notes

- Only `play_` stream IDs are recorded — auto-discovery converts `live_` → `play_` automatically
- MKV is used over MP4 for crash safety — completed segments are always intact even if the system loses power mid-recording
- `stream_ids.txt` is the single source of truth — both manual entries and auto-discovered entries live here and can be mixed freely
- The recorder Docker container and auto-discovery systemd service are independent — either can be restarted without affecting the other

</details>

---

## 🙏 Credits

Built on top of:
- [OpenIRL/srtla-receiver](https://github.com/OpenIRL/srtla-receiver)
- [OpenIRL/srtla](https://github.com/OpenIRL/srtla)
- [OpenIRL/srt-live-server](https://github.com/OpenIRL/srt-live-server)

---

## 📢 Disclaimer

This is a personal project, built and maintained in my own time. It works well for my use case but comes with no guarantees. Updates will be infrequent — likely only when breaking changes occur in [OpenIRL/srtla-receiver](https://github.com/OpenIRL/srtla-receiver) or significant new features are worth adding. Issues and pull requests are welcome but response times may vary.

---

## 📄 License

This project is free and open. Do whatever you want with it.

You are free to use, copy, modify, merge, publish, distribute, and build upon this project — for personal or commercial purposes — with no restrictions and no requirement to credit the original author.

**This software is provided as-is, with no warranty of any kind.** The author is not responsible for any data loss, hardware issues, or other problems that may arise from its use. Use it at your own risk.
