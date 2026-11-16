#!/bin/bash
# Installs or updates IRL Auto Recorder next to an OpenIRL srtla-receiver.
# Run from the repo folder:  ./install.sh
set -euo pipefail
cd "$(dirname "$0")"

say()  { printf '\033[1;36m%s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m%s\033[0m\n' "$*"; }

command -v docker >/dev/null || { echo "Docker is not installed."; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "Docker Compose v2 is not installed."; exit 1; }

# Ports from the running receiver, so the defaults match your setup.
stats_port=8080
player_port=4000
if docker inspect srtla-receiver >/dev/null 2>&1; then
    p=$(docker port srtla-receiver 8080/tcp 2>/dev/null | head -1 | awk -F: '{print $NF}')
    [ -n "$p" ] && stats_port=$p
    p=$(docker port srtla-receiver 4000/udp 2>/dev/null | head -1 | awk -F: '{print $NF}')
    [ -n "$p" ] && player_port=$p
    say "Found srtla-receiver: stats port $stats_port, player port $player_port"
else
    warn "No srtla-receiver container found; using default ports 8080 / 4000."
fi

if [ ! -f .env ]; then
    say "Creating .env"
    cp .env.example .env
    sed -i "s|^RECORDINGS_PATH=.*|RECORDINGS_PATH=$HOME/recordings|" .env
    sed -i "s|^PUID=.*|PUID=$(id -u)|; s|^PGID=.*|PGID=$(id -g)|" .env
    sed -i "s|^STATS_URL=.*|STATS_URL=http://127.0.0.1:$stats_port|" .env
    sed -i "s|^SRT_PLAYER=.*|SRT_PLAYER=127.0.0.1:$player_port|" .env
    echo
    echo "Paste the receiver's API key (the one the management web UI uses)."
    echo "Leave it empty to only record IDs listed in recordings/stream_ids.txt."
    read -r -s -p "API key: " key; echo
    if [ -n "$key" ]; then
        sed -i "s|^SLS_API_KEY=.*|SLS_API_KEY=$key|" .env
    fi
    chmod 600 .env
else
    say "Keeping existing .env"
fi

rec_path=$(grep -E '^RECORDINGS_PATH=' .env | cut -d= -f2-)
mkdir -p "${rec_path:-./recordings}"

# The old version used separate host services; the recorder now does both jobs.
for svc in openirl-discovery openirl-cleanup; do
    if systemctl list-unit-files "$svc.service" --no-legend 2>/dev/null | grep -q "$svc"; then
        warn "Turning off old $svc service (replaced by the recorder)"
        sudo systemctl disable --now "$svc.service" || warn "Could not stop $svc; do it manually."
    fi
done

# A recorder container from another folder (e.g. version 1) would block the name.
if docker inspect irl-auto-recorder >/dev/null 2>&1; then
    old_dir=$(docker inspect irl-auto-recorder --format '{{index .Config.Labels "com.docker.compose.project.working_dir"}}')
    if [ "$old_dir" != "$PWD" ]; then
        warn "Removing old irl-auto-recorder container (from ${old_dir:-unknown folder}); its files are kept"
        docker rm -f irl-auto-recorder >/dev/null
    fi
fi

say "Building and starting the recorder"
docker compose up -d --build
echo
say "Done. Follow the log with:  docker logs -f irl-auto-recorder"
