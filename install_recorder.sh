#!/bin/bash
#
# Interactive Installation script for OpenIRL Auto-Recorder
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎬 OpenIRL Auto-Recorder Installer${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found!${NC}"
    echo "Please install Docker first: curl -fsSL https://get.docker.com | sh"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found!${NC}"
    echo "Please install Docker Compose V2"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose found${NC}"

# Check OpenIRL
if ! docker ps | grep -q srtla-receiver; then
    echo -e "${YELLOW}⚠️  OpenIRL container not found${NC}"
    echo "Make sure OpenIRL/SRTLA is installed and running"
    read -p "Continue anyway? [y/N]: " CONTINUE
    if [[ ! $CONTINUE =~ ^[Yy]$ ]]; then
        exit 0
    fi
else
    echo -e "${GREEN}✓ OpenIRL found${NC}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 Configuration${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Get OpenIRL stats host
echo "OpenIRL Stats API Host"
echo "This is usually 127.0.0.1 if OpenIRL is on the same machine"
read -p "Stats Host:Port [127.0.0.1:8080]: " STATS_HOST
STATS_HOST=${STATS_HOST:-127.0.0.1:8080}

# Get SRT caller host
echo ""
echo "SRT Player Port"
echo "This is the port your streams play from (default: 4000)"
read -p "SRT Host:Port [127.0.0.1:4000]: " SRT_HOST
SRT_HOST=${SRT_HOST:-127.0.0.1:4000}

# Segment duration
echo ""
read -p "Recording segment duration in minutes [15]: " SEG_MIN
SEG_MIN=${SEG_MIN:-15}
SEGMENT_DURATION=$((SEG_MIN * 60))

# Disconnect grace
echo ""
read -p "Disconnect grace period in seconds [90]: " DISCONNECT_GRACE
DISCONNECT_GRACE=${DISCONNECT_GRACE:-90}

echo ""
echo -e "${GREEN}Summary:${NC}"
echo "  Stats API: $STATS_HOST"
echo "  SRT Player: $SRT_HOST"  
echo "  Segment duration: ${SEG_MIN} minutes"
echo "  Disconnect grace: ${DISCONNECT_GRACE} seconds"
echo "  Recordings: ~/recordings"
echo ""

read -p "Continue with installation? [y/N]: " CONFIRM
if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    exit 0
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}📦 Installing...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Create directories
echo "📁 Creating directories..."
mkdir -p ~/recordings
mkdir -p ~/irl-auto-recorder

# Copy files
echo "📋 Copying files..."
cp auto_recorder.py ~/irl-auto-recorder/
cp Dockerfile ~/irl-auto-recorder/
cp docker-compose.yml ~/irl-auto-recorder/

# Update docker-compose with user's settings
echo "⚙️  Configuring docker-compose..."
sed -i "s|STATS_HOST=127.0.0.1:8080|STATS_HOST=$STATS_HOST|" ~/irl-auto-recorder/docker-compose.yml
sed -i "s|SRT_CALLER_HOST=127.0.0.1:4000|SRT_CALLER_HOST=$SRT_HOST|" ~/irl-auto-recorder/docker-compose.yml
sed -i "s|SEGMENT_DURATION=900|SEGMENT_DURATION=$SEGMENT_DURATION|" ~/irl-auto-recorder/docker-compose.yml
sed -i "s|DISCONNECT_GRACE=90|DISCONNECT_GRACE=$DISCONNECT_GRACE|" ~/irl-auto-recorder/docker-compose.yml

# Create stream_ids.txt
echo "📝 Creating stream_ids.txt..."
if [ ! -f ~/recordings/stream_ids.txt ]; then
    cat > ~/recordings/stream_ids.txt << 'EOF'
# OpenIRL Auto-Recorder Stream List
# Add your play_ stream IDs here, one per line
# Example: play_123456789012
#
# Lines starting with # are comments and will be ignored

EOF
fi

# Set permissions
chmod 644 ~/recordings/stream_ids.txt
chmod +x ~/irl-auto-recorder/auto_recorder.py

# Build and start
echo ""
echo "🔨 Building Docker container..."
cd ~/irl-auto-recorder
docker compose up -d --build

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Installation complete!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

sleep 2

echo -e "${GREEN}📊 Container status:${NC}"
docker ps | grep irl-auto-recorder

echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo ""
echo "1. Add your stream IDs:"
echo "   nano ~/recordings/stream_ids.txt"
echo ""
echo "2. View logs:"
echo "   docker logs -f irl-auto-recorder"
echo ""
echo "3. Useful commands:"
echo "   Start:   cd ~/irl-auto-recorder && docker compose up -d"
echo "   Stop:    cd ~/irl-auto-recorder && docker compose down"
echo "   Restart: cd ~/irl-auto-recorder && docker compose restart"
echo "   Logs:    docker logs -f irl-auto-recorder"
echo ""
