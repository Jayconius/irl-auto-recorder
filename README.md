# 🎬 OpenIRL Auto-Recorder

Automatically records every stream on an [OpenIRL/srtla-receiver](https://github.com/OpenIRL/srtla-receiver) to segmented MKV files, and cleans up old recordings when the disk fills up.

![Docker](https://img.shields.io/badge/Docker-required-2496ED?logo=docker&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-x86%20%7C%20ARM-lightgrey)
![License](https://img.shields.io/badge/License-Unlicense-green)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-compatible-C51A4A?logo=raspberrypi&logoColor=white)

---

## ✨ Features

- 🔑 **Follows your receiver's profiles.** Every stream profile in the receiver's web UI is recorded, including new ones before their first stream. Deleted profiles are dropped automatically.
- 🎬 **Records only when live.** Recording starts when someone goes live and stops when they've been offline for 90 seconds, so brief drops on mobile connections don't split the recording.
- 📁 **Organised, crash-safe files.** Recordings are 15-minute MKV segments in `recordings/<stream>/<date>/`.
- 🧹 **Disk cleanup.** When the disk passes 85%, the oldest recordings are deleted until it's back under 75%.
- 🩺 **Health check.** Docker marks the container unhealthy if the recorder stops working.
- 🐳 **One container.** No host services and no extra permissions. Works on x86 and ARM (Raspberry Pi).

---

## 📋 Requirements

- [OpenIRL/srtla-receiver](https://github.com/OpenIRL/srtla-receiver) running on the same machine
- Docker with Docker Compose v2
- The receiver's **API key** (the key the management web UI asks for)

---

## ⚡ Install

```bash
git clone https://github.com/Jayconius/irl-auto-recorder.git
cd irl-auto-recorder
./install.sh
```

The installer reads the ports from your running `srtla-receiver`, asks for the API key, writes `.env`, and starts the container. If the old discovery/cleanup services from version 1 are installed, it turns them off because the recorder now handles both jobs.

Check it's working:

```bash
docker logs -f irl-auto-recorder
```

You should see a `➕ Tracking play_...` line for each of your profiles.

### Changing the API key

```bash
./install.sh --set-key
```

The key is checked against the receiver before it's saved, and the recorder restarts with it.

### Updating

```bash
cd irl-auto-recorder
git pull
docker compose up -d --build
```

### Manual install

```bash
cp .env.example .env
nano .env                 # set SLS_API_KEY, RECORDINGS_PATH, ports
docker compose up -d --build
```

---

## ⚙️ Configuration (`.env`)

| Setting | Default | What it does |
|---|---|---|
| `SLS_API_KEY` | (empty) | Receiver API key. Without it, only IDs listed in `stream_ids.txt` are recorded. |
| `RECORDINGS_PATH` | `./recordings` | Folder on this machine where recordings go |
| `STATS_URL` | `http://127.0.0.1:8080` | Receiver stats/API address (`SLS_STATS_PORT` in the receiver's `.env`) |
| `SRT_PLAYER` | `127.0.0.1:4000` | Receiver player address (`SRT_PLAYER_PORT`) |
| `SEGMENT_SECONDS` | `900` | Length of each file |
| `GRACE_SECONDS` | `90` | How long a stream can be offline before the recording stops |
| `EXCLUDE_STREAM_IDS` | (empty) | Comma-separated player IDs never to record |
| `CLEANUP_START_PERCENT` | `85` | Disk use that triggers cleanup (`0` turns cleanup off) |
| `CLEANUP_TARGET_PERCENT` | `75` | Cleanup deletes oldest recordings until disk use is below this |
| `PUID` / `PGID` | `1000` | User the container runs as, so you own the files |

After changing `.env`, apply it with `docker compose up -d`.

> [!TIP]
> For the API key, a **read-only** key is enough. You can create one with your admin key:
> ```bash
> curl -X POST http://127.0.0.1:8080/api/keys \
>   -H "Authorization: Bearer YOUR_ADMIN_KEY" -H "Content-Type: application/json" \
>   -d '{"name":"auto-recorder","permissions":"read"}'
> ```

### Extra stream IDs

To record a player ID that isn't a profile on the receiver, add it to `recordings/stream_ids.txt`, one per line. Lines starting with `#` are ignored.

---

## 📁 Recordings

```
recordings/
├── stream_ids.txt                      (optional extra IDs)
└── play_yourstream/
    └── 2026-11-16/
        ├── play_yourstream_20261116_201500_part000.mkv
        └── play_yourstream_20261116_201500_part001.mkv
```

Files are split on the clock (:00, :15, :30, :45), so a crash or power cut loses at most the segment being written.

| Drive type | Filesystem |
|---|---|
| SSD / USB SSD | ext4 |
| Shared with Windows | exFAT |

> ⚠️ **Avoid FAT32.** Its 4 GB file limit will break long recordings.

---

## 🛠️ Troubleshooting

| Log message | Fix |
|---|---|
| `API key rejected` | Check `SLS_API_KEY` in `.env`, then run `docker compose up -d` |
| `Stats unreachable` | Check `STATS_URL` matches the receiver's stats port (`docker port srtla-receiver`) |
| `ffmpeg failed ... Connection setup failure` | Check `SRT_PLAYER` matches the receiver's player port |
| No `➕ Tracking` lines | No profiles yet: create one in the receiver's web UI |

Container status, including the health check:

```bash
docker ps --filter name=irl-auto-recorder
```

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
