#!/usr/bin/env python3
"""
OpenIRL Stream ID Auto-Discovery
Monitors OpenIRL logs for new incoming streams and automatically adds them to stream_ids.txt
"""

import subprocess
import re
import time
import os
from datetime import datetime

# Configuration
STREAM_IDS_FILE = os.path.expanduser("~/recordings/stream_ids.txt")
OPENIRL_CONTAINER = "srtla-receiver"
CHECK_INTERVAL = 5  # Check logs every 5 seconds

# Track stream IDs we've already seen
known_stream_ids = set()


def log(msg):
    """Print timestamped log message"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def load_existing_stream_ids():
    """Load stream IDs that are already in the file"""
    stream_ids = set()
    try:
        if os.path.exists(STREAM_IDS_FILE):
            with open(STREAM_IDS_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and line.startswith('play_'):
                        stream_ids.add(line)
    except Exception as e:
        log(f"⚠️  Error loading existing stream IDs: {e}")
    return stream_ids


def add_stream_id_to_file(stream_id):
    """Add a new stream ID to the file"""
    try:
        with open(STREAM_IDS_FILE, 'a') as f:
            f.write(f"{stream_id}\n")
        log(f"✅ Added to stream_ids.txt: {stream_id}")
        return True
    except Exception as e:
        log(f"❌ Error adding stream ID: {e}")
        return False


def monitor_openirl_logs():
    """
    Monitor OpenIRL logs for new stream connections
    Looks for patterns like: streamid='live_xxxxx' or streamid='play_xxxxx'
    """
    log("🔍 Starting OpenIRL log monitor...")
    log(f"📝 Stream IDs file: {STREAM_IDS_FILE}")
    log(f"🐳 Monitoring container: {OPENIRL_CONTAINER}")
    
    # Load existing stream IDs
    global known_stream_ids
    known_stream_ids = load_existing_stream_ids()
    log(f"📋 Loaded {len(known_stream_ids)} existing stream IDs")
    
    # Keep track of last log timestamp to avoid re-processing
    last_log_time = None
    
    try:
        # Start following logs
        process = subprocess.Popen(
            ['docker', 'logs', '-f', '--since', '1m', OPENIRL_CONTAINER],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        log("✅ Log monitoring started")
        
        # Regex patterns to match stream IDs in logs
        # Looks for: streamid='live_xxxxx' or streamid="live_xxxxx" or stream_id=live_xxxxx
        patterns = [
            r"streamid[=:]\s*['\"]?(live_[a-zA-Z0-9_]+)['\"]?",
            r"streamid[=:]\s*['\"]?(play_[a-zA-Z0-9_]+)['\"]?",
            r"stream_name[=:]\s*['\"]?(live_[a-zA-Z0-9_]+)['\"]?",
            r"stream_name[=:]\s*['\"]?(play_[a-zA-Z0-9_]+)['\"]?",
        ]
        
        for line in process.stdout:
            line = line.strip()
            
            # Try each pattern
            for pattern in patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                
                for stream_id in matches:
                    # Convert live_ to play_ for recording
                    if stream_id.startswith('live_'):
                        play_stream_id = stream_id.replace('live_', 'play_', 1)
                    else:
                        play_stream_id = stream_id
                    
                    # Check if this is a new stream ID
                    if play_stream_id not in known_stream_ids and play_stream_id.startswith('play_'):
                        log(f"🆕 Discovered new stream: {stream_id} → {play_stream_id}")
                        
                        # Add to file
                        if add_stream_id_to_file(play_stream_id):
                            known_stream_ids.add(play_stream_id)
                            log(f"📊 Total tracked streams: {len(known_stream_ids)}")
    
    except KeyboardInterrupt:
        log("\n⏹️  Stopping log monitor...")
    except Exception as e:
        log(f"❌ Error monitoring logs: {e}")
    finally:
        if 'process' in locals():
            process.kill()


def main():
    """Main loop"""
    log("🚀 OpenIRL Stream ID Auto-Discovery started")
    
    # Ensure stream_ids.txt exists
    os.makedirs(os.path.dirname(STREAM_IDS_FILE), exist_ok=True)
    if not os.path.exists(STREAM_IDS_FILE):
        with open(STREAM_IDS_FILE, 'w') as f:
            f.write("# OpenIRL Auto-Recorder Stream List\n")
            f.write("# Auto-discovered stream IDs will be added below\n")
            f.write("#\n")
    
    # Start monitoring
    monitor_openirl_logs()
    
    log("✅ Auto-discovery stopped")


if __name__ == "__main__":
    main()
