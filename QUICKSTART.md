# ⚡ Quick Start Guide

> Before you begin, make sure [OpenIRL/srtla-receiver](https://github.com/OpenIRL/srtla-receiver) is installed and running.

---

## Step 1 — Upload Files

Upload all files to your server:

```bash
mkdir -p ~/irl-auto-recorder
cd ~/irl-auto-recorder
```

Place these files in the folder:
- `auto_recorder.py`
- `Dockerfile`
- `docker-compose.yml`
- `install_recorder.sh`
- `stream_auto_discovery.py`
- `install_discovery.sh`
- `openirl-discovery.service`
- `install_cleanup.sh` *(if using auto-cleanup)*

---

## Step 2 — Install the Recorder

```bash
chmod +x install_recorder.sh
./install_recorder.sh
```

Press **Enter** to accept all defaults.

---

## Step 3 — Install Auto-Discovery

```bash
chmod +x install_discovery.sh
./install_discovery.sh
```

---

## Step 4 — Install Auto-Cleanup *(Optional)*

```bash
chmod +x install_cleanup.sh
./install_cleanup.sh
```

Press **Enter** to accept all defaults.

---

## Step 5 — Add Your Stream IDs

```bash
nano ~/recordings/stream_ids.txt
```

Add your stream IDs, one per line:
```
play_yourstream1
play_yourstream2
```

Save with `Ctrl+O`, `Enter`, `Ctrl+X`.

---

## Step 6 — Verify Everything is Running

```bash
# Check recorder is running
docker ps | grep irl-auto-recorder

# Check recorder logs
docker logs -f irl-auto-recorder

# Check auto-discovery
sudo systemctl status openirl-discovery
```

---

## ✅ You're Done!

New streams will now be discovered and recorded automatically.

> 💡 **Tip:** Keep streaming for at least 60 seconds on first connection to ensure recording starts.

---

## 🔧 Quick Reference

```bash
# View recorder logs
docker logs -f irl-auto-recorder

# Restart recorder
cd ~/irl-auto-recorder && docker compose restart

# View auto-discovery logs
sudo journalctl -u openirl-discovery -f

# Check disk space
df -h /

# View today's recordings
ls -lh ~/recordings/*/$(date +%Y-%m-%d)/
```

---

> 📖 For full documentation see [README.md](README.md)
