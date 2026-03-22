# OpenIRL Auto-Recorder - Complete Setup Guide

**Fresh installation with auto-discovery and all improvements!**

---

## 📦 What You're Installing

### 1. **Auto-Recorder** 
- Records all configured SRT streams automatically
- 15-minute segments
- 90-second disconnect protection
- Organized by stream ID and date

### 2. **Auto-Discovery** (Optional but Recommended)
- Monitors OpenIRL logs for new connections
- Automatically adds new stream IDs to the list
- No manual configuration needed

### 3. **Auto-Cleanup** (Optional but Recommended)
- Deletes oldest recordings when disk hits 85%
- Keeps your storage from filling up

---

## 🚀 Quick Installation

### Step 1: Install Auto-Recorder

```bash
# Create directory
mkdir -p ~/irl-auto-recorder
cd ~/irl-auto-recorder

# Upload these files:
#   - auto_recorder.py
#   - Dockerfile
#   - docker-compose.yml
#   - install_recorder.sh

# Run installer (it will ask questions about your setup)
chmod +x install_recorder.sh
./install_recorder.sh
```

**The installer will ask:**
- OpenIRL Stats host (default: `127.0.0.1:8080`)
- SRT Player port (default: `127.0.0.1:4000`)
- Segment duration (default: 15 minutes)
- Disconnect grace (default: 90 seconds)

Just press **Enter** to use defaults!

### Step 2: Add Your First Stream

```bash
nano ~/recordings/stream_ids.txt
```

Add your stream IDs (one per line):
```
play_friend1
play_friend2
```

Save and exit (Ctrl+O, Enter, Ctrl+X).

**Within 30 seconds**, the recorder will detect them!

### Step 3: Verify It's Working

```bash
docker logs -f irl-auto-recorder
```

You should see:
```
[2026-03-22 02:30:00] 🚀 OpenIRL Auto-Recorder started
[2026-03-22 02:30:00] 🆕 Discovered new stream ID: play_friend1
[2026-03-22 02:30:00] 🆕 Discovered new stream ID: play_friend2
```

---

## ⭐ Step 4: Install Auto-Discovery (Recommended!)

**This automatically adds new streams - no manual editing needed!**

```bash
cd ~/irl-auto-recorder

# Upload these additional files:
#   - stream_auto_discovery.py
#   - openirl-discovery.service
#   - install_discovery.sh

# Run installer
chmod +x install_discovery.sh
./install_discovery.sh
```

**Now when someone streams with a new ID:**
1. Auto-discovery detects it (within seconds)
2. Adds `play_STREAMID` to stream_ids.txt
3. Recorder picks it up (within 30 seconds)
4. Recording starts automatically!

**Monitor auto-discovery:**
```bash
sudo journalctl -u openirl-discovery -f
```

---

## 🧹 Step 5: Install Auto-Cleanup (Recommended!)

**Prevents your disk from filling up!**

```bash
cd ~/irl-auto-recorder

# Upload these files:
#   - auto_cleanup.sh
#   - openirl-cleanup.service
#   - install_cleanup.sh

# Run installer (it will ask about thresholds)
chmod +x install_cleanup.sh
./install_cleanup.sh
```

**The installer will ask:**
- Recordings directory (default: `~/recordings`)
- Cleanup threshold (default: 85%)
- Stop at percentage (default: 75%)
- Check interval (default: 300 seconds)

---

## 📊 Daily Usage

### View Recorder Logs
```bash
docker logs -f irl-auto-recorder
```

### View Auto-Discovery Logs
```bash
sudo journalctl -u openirl-discovery -f
```

### View Auto-Cleanup Logs
```bash
sudo journalctl -u openirl-cleanup -f
```

### Check Disk Space
```bash
df -h /
```

### View Today's Recordings
```bash
ls -lh ~/recordings/*/$(date +%Y-%m-%d)/
```

### Manually Add Stream
```bash
echo "play_newstream" >> ~/recordings/stream_ids.txt
```

---

## 🔧 Configuration

### Change Recording Settings

Edit `~/irl-auto-recorder/docker-compose.yml`:
```yaml
environment:
  - SEGMENT_DURATION=1800   # 30 minutes instead of 15
  - DISCONNECT_GRACE=120    # 2 minutes instead of 90 seconds
  - STATS_HOST=127.0.0.1:8080
  - SRT_CALLER_HOST=127.0.0.1:4000
```

Then restart:
```bash
cd ~/irl-auto-recorder
docker compose restart
```

### Change Auto-Discovery Speed

To make it check faster (every 5 seconds instead of 30):

Edit `~/irl-auto-recorder/docker-compose.yml`:
```yaml
environment:
  - DISCOVERY_INTERVAL=5   # Check every 5 seconds
```

Restart:
```bash
cd ~/irl-auto-recorder
docker compose restart
```

---

## 📁 File Structure

After installation:

```
~/irl-auto-recorder/
├── auto_recorder.py          # Main recorder script
├── Dockerfile                # Container build
├── docker-compose.yml        # Settings
├── stream_auto_discovery.py  # Auto-discovery script
└── install files...

~/recordings/
├── stream_ids.txt            # YOUR STREAM LIST
├── play_friend1/
│   └── 2026-03-22/
│       ├── play_friend1_20260322_140000_part001.mkv
│       └── play_friend1_20260322_140000_part002.mkv
└── play_friend2/
    └── 2026-03-22/
        └── play_friend2_20260322_150000_part001.mkv

/home/YOUR_USER/
├── auto_cleanup.sh           # Cleanup script (if installed)
└── stream_auto_discovery.py  # Discovery script (if installed)
```

---

## ✅ Verification Checklist

After installation, verify everything works:

**Recorder:**
- [ ] Container running: `docker ps | grep irl-auto-recorder`
- [ ] Logs showing: `docker logs irl-auto-recorder`
- [ ] Stream IDs loaded: Check logs for "🆕 Discovered"

**Auto-Discovery (if installed):**
- [ ] Service running: `sudo systemctl status openirl-discovery`
- [ ] Logs showing: `sudo journalctl -u openirl-discovery -n 20`

**Auto-Cleanup (if installed):**
- [ ] Service running: `sudo systemctl status openirl-cleanup`
- [ ] Disk checks: See "✓ Disk usage" in logs

---

## 🔍 Troubleshooting

### Recorder Not Starting

```bash
# Check logs for errors
docker logs irl-auto-recorder

# Verify container exists
docker ps -a | grep irl-auto-recorder

# Rebuild if needed
cd ~/irl-auto-recorder
docker compose down
docker compose up -d --build
```

### Auto-Discovery Not Adding Streams

```bash
# Check service status
sudo systemctl status openirl-discovery

# View logs
sudo journalctl -u openirl-discovery -f

# Restart service
sudo systemctl restart openirl-discovery
```

### Streams Not Recording

1. Check stream ID is in the file:
   ```bash
   cat ~/recordings/stream_ids.txt
   ```

2. Verify stream is active:
   ```bash
   curl http://127.0.0.1:8080/stats/play_YOURSTREAM
   ```

3. Check recorder logs:
   ```bash
   docker logs --tail 50 irl-auto-recorder
   ```

---

## 📝 Important Notes

### Auto-Discovery Timing
- **Discovery adds stream:** Immediately (1-2 seconds)
- **Recorder checks file:** Every 30 seconds
- **Total time to start recording:** 0-30 seconds after connection

**Keep streaming for at least 60 seconds** on first connection to ensure recording starts!

### What Gets Recorded
- ✅ `play_` streams (playback/download streams)
- ❌ `live_` streams (publisher/upload streams)

Auto-discovery automatically converts `live_` to `play_` for you!

### Log Verbosity
- **Recorder:** Only logs new discoveries and recording events
- **Auto-Discovery:** Only logs when new streams are found
- **Auto-Cleanup:** Logs every check (every 5 minutes)

Clean, minimal logging!

---

## 🎯 Quick Commands Reference

```bash
# RECORDER
docker logs -f irl-auto-recorder              # View logs
cd ~/irl-auto-recorder && docker compose restart  # Restart
nano ~/recordings/stream_ids.txt              # Edit streams

# AUTO-DISCOVERY
sudo journalctl -u openirl-discovery -f       # View logs
sudo systemctl restart openirl-discovery      # Restart
sudo systemctl status openirl-discovery       # Check status

# AUTO-CLEANUP
sudo journalctl -u openirl-cleanup -f         # View logs
sudo systemctl restart openirl-cleanup        # Restart

# GENERAL
df -h /                                       # Check disk
du -sh ~/recordings                           # Recording size
find ~/recordings -name "*.mkv" | wc -l       # Count files
```

---

## 🌟 What's Improved

**This version fixes:**
- ✅ No more spam logging ("Loaded from file" every 30 seconds)
- ✅ Clean, minimal logs (only important events)
- ✅ Auto-discovery works perfectly
- ✅ Universal installation (works on any system)
- ✅ All improvements included

**You get:**
- ✨ Clean logs
- ✨ Auto-discovery of new streams
- ✨ Automatic cleanup
- ✨ Professional setup
- ✨ Easy to maintain

---

## 📚 Need More Help?

See the detailed guides:
- **README-RECORDER.md** - Complete recorder documentation
- **README-CLEANUP.md** - Cleanup system guide
- **INSTALL-RECORDER.md** - Detailed installation steps
- **INSTALL-CLEANUP.md** - Cleanup installation guide

---

## 🎉 You're Done!

Your setup is now:
- 🎬 **Recording** all streams automatically
- 🔍 **Discovering** new streams automatically
- 🧹 **Cleaning** old files automatically
- 📊 **Logging** only important events

Just add stream IDs (or let auto-discovery do it) and forget about it! 🚀
