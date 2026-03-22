#!/usr/bin/env python3
"""
OpenIRL Auto Stream Recorder
Automatically discovers and records all incoming SRT streams
"""

import subprocess
import os
import time
import json
import urllib.request
from datetime import datetime
from collections import defaultdict

# ========== CONFIGURATION ==========
# These can be overridden by environment variables
STATS_HOST = os.environ.get('STATS_HOST', '127.0.0.1:8080')
SRT_CALLER_HOST = os.environ.get('SRT_CALLER_HOST', '127.0.0.1:4000')
RECORDINGS_BASE = os.environ.get('RECORDINGS_BASE', os.path.expanduser('~/recordings'))
SEGMENT_DURATION = int(os.environ.get('SEGMENT_DURATION', '900'))  # 15 minutes in seconds
DISCONNECT_GRACE = int(os.environ.get('DISCONNECT_GRACE', '90'))   # 90 seconds grace period
POLL_INTERVAL = int(os.environ.get('POLL_INTERVAL', '10'))         # Check for streams every 10 seconds
DISCOVERY_INTERVAL = int(os.environ.get('DISCOVERY_INTERVAL', '30'))  # Check file for new streams every 30 seconds

# ========== STATE TRACKING ==========
active_recordings = {}  # stream_id -> {process, last_seen, start_time}
stream_offline_timers = {}  # stream_id -> timestamp when went offline
known_stream_ids = set()  # All stream IDs we know about
last_discovery_time = 0  # Last time we checked for new streams


def log(msg):
    """Print timestamped log message"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def load_stream_ids_from_file():
    """
    Load stream IDs from a text file if it exists
    File format: one stream ID per line
    """
    stream_file = os.path.join(RECORDINGS_BASE, "stream_ids.txt")
    stream_ids = set()
    
    try:
        if os.path.exists(stream_file):
            with open(stream_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith('#') and line.startswith('play_'):
                        stream_ids.add(line)
                        # Don't log every read, only new discoveries
    except Exception as e:
        log(f"⚠️  Could not read stream_ids.txt: {e}")
    
    return stream_ids


def check_stream_stats(stream_id):
    """
    Check if a stream is currently active via stats API
    Returns: dict with stream stats if active, None if offline
    """
    try:
        url = f"http://{STATS_HOST}/stats/{stream_id}"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            
            # Check if publisher is actually streaming
            if data.get("status") == "ok" and "publisher" in data:
                return data
            return None
    except Exception:
        return None


def discover_new_streams():
    """
    Discover new stream IDs from the text file
    """
    new_ids = set()
    
    # Load from text file
    file_ids = load_stream_ids_from_file()
    new_ids.update(file_ids)
    
    # Add newly discovered IDs to our known set
    for stream_id in new_ids:
        if stream_id not in known_stream_ids:
            known_stream_ids.add(stream_id)
            log(f"🆕 Discovered new stream ID: {stream_id}")
    
    return known_stream_ids


def discover_active_streams():
    """
    Check which known streams are currently active
    """
    active = set()
    
    for stream_id in known_stream_ids:
        # Only check play_ streams, skip live_ streams
        if not stream_id.startswith('play_'):
            continue
        
        if check_stream_stats(stream_id):
            active.add(stream_id)
    
    return active


def get_stream_folder(stream_id):
    """
    Create organized folder structure for recordings
    Format: /recordings/play_XXXXX/YYYY-MM-DD/
    """
    today = datetime.now().strftime('%Y-%m-%d')
    folder = os.path.join(RECORDINGS_BASE, stream_id, today)
    os.makedirs(folder, exist_ok=True)
    return folder


def start_recording(stream_id):
    """
    Start FFmpeg recording for a stream with 15-minute segmentation
    """
    folder = get_stream_folder(stream_id)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Filename pattern for segments
    filename_pattern = os.path.join(folder, f"{stream_id}_{timestamp}_part%03d.mkv")
    
    # SRT URL to connect to OpenIRL
    srt_url = f"srt://{SRT_CALLER_HOST}?mode=caller&streamid={stream_id}"
    
    # FFmpeg command with segmentation
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-i", srt_url,
        "-map", "0",
        "-c", "copy",
        "-f", "segment",
        "-segment_time", str(SEGMENT_DURATION),
        "-reset_timestamps", "1",
        "-segment_format", "matroska",
        "-segment_atclocktime", "1",
        filename_pattern
    ]
    
    log(f"🎬 STARTING recording: {stream_id}")
    log(f"   📁 Saving to: {folder}")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        active_recordings[stream_id] = {
            'process': process,
            'last_seen': time.time(),
            'start_time': datetime.now(),
            'folder': folder
        }
        
        return True
    except Exception as e:
        log(f"❌ ERROR starting recording for {stream_id}: {e}")
        return False


def stop_recording(stream_id):
    """
    Stop recording for a stream
    """
    if stream_id not in active_recordings:
        return
    
    rec = active_recordings[stream_id]
    process = rec['process']
    
    log(f"🛑 STOPPING recording: {stream_id}")
    duration = datetime.now() - rec['start_time']
    log(f"   ⏱️  Duration: {duration}")
    
    try:
        process.terminate()
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
    except Exception as e:
        log(f"⚠️  Error stopping {stream_id}: {e}")
    
    del active_recordings[stream_id]
    if stream_id in stream_offline_timers:
        del stream_offline_timers[stream_id]


def main_loop():
    """
    Main monitoring loop
    """
    global last_discovery_time
    
    log("🚀 OpenIRL Auto-Recorder started")
    log(f"📊 Monitoring: {STATS_HOST}")
    log(f"💾 Recordings: {RECORDINGS_BASE}")
    log(f"⏱️  Segment duration: {SEGMENT_DURATION}s ({SEGMENT_DURATION//60} min)")
    log(f"🔌 Disconnect grace period: {DISCONNECT_GRACE}s")
    log(f"")
    log(f"📝 To add streams, edit: {os.path.join(RECORDINGS_BASE, 'stream_ids.txt')}")
    log(f"   Add one stream ID per line (e.g., play_123456789012)")
    log(f"   Or use auto-discovery to add them automatically!")
    log(f"")
    log(f"🔍 Checking for streams...")
    
    # Initial discovery
    discover_new_streams()
    last_discovery_time = time.time()
    
    if not known_stream_ids:
        log(f"⚠️  No stream IDs found in stream_ids.txt")
        log(f"   Add stream IDs manually or wait for auto-discovery")
    
    while True:
        try:
            current_time = time.time()
            
            # Periodically check for new streams
            if current_time - last_discovery_time >= DISCOVERY_INTERVAL:
                discover_new_streams()
                last_discovery_time = current_time
            
            # Check which known streams are currently active
            active_streams = discover_active_streams()
            
            # Process each active stream
            for stream_id in active_streams:
                if stream_id not in active_recordings:
                    # New stream detected - start recording
                    start_recording(stream_id)
                    # Clear any offline timer
                    if stream_id in stream_offline_timers:
                        del stream_offline_timers[stream_id]
                else:
                    # Update last seen timestamp
                    active_recordings[stream_id]['last_seen'] = current_time
                    # Clear offline timer since stream is active
                    if stream_id in stream_offline_timers:
                        del stream_offline_timers[stream_id]
            
            # Check for streams that went offline
            for stream_id in list(active_recordings.keys()):
                if stream_id not in active_streams:
                    # Stream not detected in current scan
                    if stream_id not in stream_offline_timers:
                        # First time noticing it's offline - start grace period
                        stream_offline_timers[stream_id] = current_time
                        log(f"⚠️  Stream offline: {stream_id} (grace period: {DISCONNECT_GRACE}s)")
                    else:
                        # Check if grace period expired
                        offline_duration = current_time - stream_offline_timers[stream_id]
                        if offline_duration >= DISCONNECT_GRACE:
                            log(f"💤 Grace period expired for {stream_id} ({offline_duration:.0f}s)")
                            stop_recording(stream_id)
            
            # Check for dead processes
            for stream_id in list(active_recordings.keys()):
                rec = active_recordings[stream_id]
                if rec['process'].poll() is not None:
                    # Process died
                    log(f"⚰️  Recording process died: {stream_id}")
                    try:
                        stderr_output = rec['process'].stderr.read().decode()
                        if stderr_output:
                            log(f"   ⚠️  FFmpeg error: {stderr_output[:200]}")
                    except:
                        pass
                    del active_recordings[stream_id]
                    if stream_id in stream_offline_timers:
                        del stream_offline_timers[stream_id]
            
            # Sleep before next check
            time.sleep(POLL_INTERVAL)
            
        except KeyboardInterrupt:
            log("\n⏹️  Shutting down...")
            break
        except Exception as e:
            log(f"❌ Error in main loop: {e}")
            time.sleep(POLL_INTERVAL)
    
    # Cleanup - stop all recordings
    log("🧹 Stopping all active recordings...")
    for stream_id in list(active_recordings.keys()):
        stop_recording(stream_id)
    
    log("✅ Recorder stopped")


if __name__ == "__main__":
    # Ensure recordings directory exists
    os.makedirs(RECORDINGS_BASE, exist_ok=True)
    
    # Create empty stream_ids.txt if it doesn't exist
    stream_file = os.path.join(RECORDINGS_BASE, "stream_ids.txt")
    if not os.path.exists(stream_file):
        with open(stream_file, 'w') as f:
            f.write("# OpenIRL Auto-Recorder Stream List\n")
            f.write("# Add your play_ stream IDs here, one per line\n")
            f.write("# Example: play_123456789012\n")
            f.write("#\n")
            f.write("# Lines starting with # are comments and will be ignored\n")
            f.write("# Auto-discovery will add new streams automatically\n")
            f.write("\n")
    
    main_loop()
