#!/usr/bin/env python3
"""
IRL Auto Recorder for OpenIRL srtla-receiver.

Every stream profile on the receiver is picked up from its API (no need to
stream once first), and each one is recorded automatically while it is live.

Recordings: <RECORDINGS_DIR>/<player_id>/<YYYY-MM-DD>/<player_id>_<start>_partNNN.mkv
"""

import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from datetime import datetime


# ---------------------------------------------------------------- config ---

def env_int(name, default):
    value = os.environ.get(name, "").strip()
    try:
        return int(value) if value else default
    except ValueError:
        sys.exit(f"Config error: {name} must be a whole number, got {value!r}")


STATS_URL = os.environ.get("STATS_URL", "http://127.0.0.1:8080").rstrip("/")
SRT_PLAYER = os.environ.get("SRT_PLAYER", "127.0.0.1:4000")
API_KEY = os.environ.get("SLS_API_KEY", "").strip()
RECORDINGS_DIR = os.environ.get("RECORDINGS_DIR", "/recordings")
SEGMENT_SECONDS = env_int("SEGMENT_SECONDS", 900)    # length of each file
GRACE_SECONDS = env_int("GRACE_SECONDS", 90)         # keep recording through short drops
POLL_SECONDS = env_int("POLL_SECONDS", 5)            # how often to check who is live
SYNC_SECONDS = env_int("SYNC_SECONDS", 60)           # how often to re-read profiles (API limit: 30/min)
SRT_TIMEOUT_SECONDS = env_int("SRT_TIMEOUT_SECONDS", 10)  # ffmpeg gives up after this much silence
CLEANUP_START_PERCENT = env_int("CLEANUP_START_PERCENT", 85)    # disk use that starts a cleanup (0 = off)
CLEANUP_TARGET_PERCENT = env_int("CLEANUP_TARGET_PERCENT", 75)  # delete oldest files until below this
CLEANUP_INTERVAL_SECONDS = 300
EXCLUDE = {s.strip() for s in os.environ.get("EXCLUDE_STREAM_IDS", "").split(",") if s.strip()}
EXTRA_IDS_FILE = os.path.join(RECORDINGS_DIR, "stream_ids.txt")
HEARTBEAT_FILE = "/tmp/recorder-heartbeat"


# --------------------------------------------------------------- logging ---

def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


# ------------------------------------------------------------ receiver ---

def http_json(url, headers=None, timeout=5):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_profiles():
    """Player IDs of every profile on the receiver, or None if the API can't be read."""
    if not API_KEY:
        return None
    data = http_json(f"{STATS_URL}/api/stream-ids",
                     headers={"Authorization": f"Bearer {API_KEY}"})
    if data.get("status") != "success":
        raise RuntimeError(data.get("message", "unexpected API response"))
    return {row["player"] for row in data.get("data", []) if row.get("player")}


def read_extra_ids():
    """Optional manual list: one player ID per line, # for comments."""
    ids = set()
    try:
        with open(EXTRA_IDS_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.split("#", 1)[0].strip()
                if line:
                    ids.add(line)
    except FileNotFoundError:
        pass
    return ids


def is_live(player_id):
    """True when someone is publishing to this profile right now."""
    quoted = urllib.parse.quote(player_id, safe="")
    data = http_json(f"{STATS_URL}/stats/{quoted}")
    return bool(data.get("publisher") or data.get("publishers"))


# ------------------------------------------------------------ recording ---

class Recording:
    def __init__(self, player_id):
        self.player_id = player_id
        self.started = datetime.now()
        self.last_live = time.monotonic()
        self.stderr_tail = deque(maxlen=15)

        folder = os.path.join(RECORDINGS_DIR, player_id, f"{self.started:%Y-%m-%d}")
        os.makedirs(folder, exist_ok=True)
        pattern = os.path.join(folder, f"{player_id}_{self.started:%Y%m%d_%H%M%S}_part%03d.mkv")

        query = urllib.parse.urlencode({
            "mode": "caller",
            "streamid": player_id,
            "timeout": SRT_TIMEOUT_SECONDS * 1_000_000,   # microseconds
        })
        cmd = [
            "ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "warning",
            "-fflags", "+genpts",
            "-i", f"srt://{SRT_PLAYER}?{query}",
            # Video and audio only: data tracks some encoders add can't go in MKV.
            "-map", "0:v?", "-map", "0:a?",
            "-c", "copy",
            "-f", "segment",
            "-segment_time", str(SEGMENT_SECONDS),
            "-segment_atclocktime", "1",
            "-segment_format", "matroska",
            "-reset_timestamps", "1",
            pattern,
        ]
        self.process = subprocess.Popen(cmd, stdin=subprocess.DEVNULL,
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.PIPE, text=True,
                                        errors="replace")
        threading.Thread(target=self._drain_stderr, daemon=True).start()
        log(f"🎬 Recording {player_id} -> {folder}")

    def _drain_stderr(self):
        for line in self.process.stderr:
            self.stderr_tail.append(line.rstrip())

    def running(self):
        return self.process.poll() is None

    def stop(self, reason):
        if self.running():
            # SIGINT lets ffmpeg finish the current file cleanly.
            self.process.send_signal(signal.SIGINT)
            try:
                self.process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        minutes = (datetime.now() - self.started).total_seconds() / 60
        log(f"🛑 Stopped {self.player_id} after {minutes:.1f} min ({reason})")


# -------------------------------------------------------------- cleanup ---

def disk_percent():
    usage = shutil.disk_usage(RECORDINGS_DIR)
    return usage.used * 100 / usage.total


def cleanup_disk():
    """Delete the oldest recordings once the disk passes CLEANUP_START_PERCENT."""
    if CLEANUP_START_PERCENT <= 0 or disk_percent() < CLEANUP_START_PERCENT:
        return
    log(f"🧹 Disk at {disk_percent():.0f}%, deleting oldest recordings "
        f"until below {CLEANUP_TARGET_PERCENT}%")
    cutoff = time.time() - 120   # never touch files still being written
    files = []
    for root, _, names in os.walk(RECORDINGS_DIR):
        for name in names:
            if name.endswith(".mkv"):
                path = os.path.join(root, name)
                try:
                    mtime = os.path.getmtime(path)
                except OSError:
                    continue
                if mtime < cutoff:
                    files.append((mtime, path))
    files.sort()

    deleted = 0
    for _, path in files:
        if disk_percent() < CLEANUP_TARGET_PERCENT or deleted >= 1000:
            break
        try:
            os.remove(path)
            deleted += 1
            log(f"   🗑️  {os.path.relpath(path, RECORDINGS_DIR)}")
        except OSError as e:
            log(f"   ⚠️  Could not delete {path}: {e}")

    # Remove day/stream folders left empty (never the recordings folder itself).
    for root, dirs, names in os.walk(RECORDINGS_DIR, topdown=False):
        if root != RECORDINGS_DIR and not dirs and not names:
            try:
                os.rmdir(root)
            except OSError:
                pass
    log(f"🧹 Deleted {deleted} file(s), disk now {disk_percent():.0f}%")


# ----------------------------------------------------------------- main ---

class Recorder:
    def __init__(self):
        self.tracked = set()
        self.api_profiles = set()
        self.recordings = {}
        self.last_sync = 0.0
        self.last_cleanup = 0.0
        self.api_problem = None
        self.stats_problem = None
        self.retry_after = {}     # player_id -> monotonic time we may retry
        self.stopping = False

    def sync_profiles(self):
        try:
            profiles = fetch_profiles()
            if self.api_problem:
                log("✅ Receiver API reachable again")
            self.api_problem = None
        except urllib.error.HTTPError as e:
            profiles = None
            problem = ("API key rejected (check SLS_API_KEY)" if e.code in (401, 403)
                       else f"API error HTTP {e.code}")
            self._report_api_problem(problem)
        except Exception as e:  # network down, receiver restarting, bad JSON...
            profiles = None
            self._report_api_problem(f"API unreachable: {e}")

        if profiles is not None:
            self.api_profiles = profiles
        # On an API failure, self.api_profiles still holds the last good list.
        wanted = (self.api_profiles | read_extra_ids()) - EXCLUDE
        for pid in sorted(wanted - self.tracked):
            log(f"➕ Tracking {pid}")
        for pid in sorted(self.tracked - wanted):
            log(f"➖ No longer tracking {pid}")
        self.tracked = wanted

    def _report_api_problem(self, problem):
        if problem != self.api_problem:
            log(f"⚠️  {problem}. Keeping the last known list of streams.")
        self.api_problem = problem

    def tick(self):
        now = time.monotonic()
        if now - self.last_sync >= SYNC_SECONDS:
            self.sync_profiles()
            self.last_sync = now
        if now - self.last_cleanup >= CLEANUP_INTERVAL_SECONDS:
            self.last_cleanup = now
            try:
                cleanup_disk()
            except OSError as e:
                log(f"⚠️  Cleanup failed: {e}")

        for pid in sorted(self.tracked | set(self.recordings)):
            try:
                live = is_live(pid)
                if self.stats_problem:
                    log("✅ Receiver stats reachable again")
                self.stats_problem = None
            except Exception as e:
                problem = f"Stats unreachable at {STATS_URL}: {e}"
                if problem != self.stats_problem:
                    log(f"⚠️  {problem}")
                self.stats_problem = problem
                return  # don't stop recordings just because stats blipped

            rec = self.recordings.get(pid)
            if rec and not rec.running():
                if rec.process.returncode == 0:
                    log(f"🔌 {pid} disconnected (will resume if it comes back)")
                else:
                    tail = " | ".join(list(rec.stderr_tail)[-3:]) or "no output"
                    log(f"⚠️  ffmpeg failed for {pid} (code {rec.process.returncode}): {tail}")
                del self.recordings[pid]
                rec = None
                self.retry_after[pid] = now + 5

            if live:
                if rec:
                    rec.last_live = now
                elif pid in self.tracked and now >= self.retry_after.get(pid, 0):
                    self.recordings[pid] = Recording(pid)
            elif rec and now - rec.last_live >= GRACE_SECONDS:
                rec.stop(f"offline for {GRACE_SECONDS}s")
                del self.recordings[pid]

    def shutdown(self, *_):
        self.stopping = True

    def run(self):
        log("🚀 IRL Auto Recorder starting")
        log(f"   Receiver stats/API: {STATS_URL}")
        log(f"   SRT player:         {SRT_PLAYER}")
        log(f"   Recordings:         {RECORDINGS_DIR}")
        log(f"   Segments {SEGMENT_SECONDS}s, grace {GRACE_SECONDS}s, poll {POLL_SECONDS}s")
        if CLEANUP_START_PERCENT > 0:
            log(f"   Cleanup at {CLEANUP_START_PERCENT}% disk, down to {CLEANUP_TARGET_PERCENT}%")
        else:
            log("   Disk cleanup off")
        if not API_KEY:
            log(f"⚠️  SLS_API_KEY not set: only recording IDs listed in {EXTRA_IDS_FILE}")
        os.makedirs(RECORDINGS_DIR, exist_ok=True)

        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)

        while not self.stopping:
            try:
                self.tick()
            except Exception as e:
                log(f"❌ Unexpected error: {e!r}")
            try:
                with open(HEARTBEAT_FILE, "w") as f:
                    f.write(str(time.time()))
            except OSError:
                pass
            for _ in range(POLL_SECONDS * 10):
                if self.stopping:
                    break
                time.sleep(0.1)

        for rec in list(self.recordings.values()):
            rec.stop("recorder shutting down")
        log("👋 Stopped")


def healthcheck():
    """Used by Docker: healthy if the main loop ran recently."""
    try:
        with open(HEARTBEAT_FILE) as f:
            age = time.time() - float(f.read())
    except (OSError, ValueError):
        return 1
    return 0 if age < max(60, POLL_SECONDS * 6) else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "healthcheck":
        sys.exit(healthcheck())
    Recorder().run()
