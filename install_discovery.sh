#!/bin/bash
#
# Installation script for OpenIRL Stream ID Auto-Discovery
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🔍 OpenIRL Stream ID Auto-Discovery Installer${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

CURRENT_USER=$(whoami)

echo -e "${YELLOW}Installing for user: ${CURRENT_USER}${NC}"
echo ""

# Copy discovery script
echo "📋 Installing auto-discovery script..."
sudo cp stream_auto_discovery.py /home/$CURRENT_USER/stream_auto_discovery.py
sudo chmod +x /home/$CURRENT_USER/stream_auto_discovery.py
sudo chown $CURRENT_USER:$CURRENT_USER /home/$CURRENT_USER/stream_auto_discovery.py

# Create service file
echo "📝 Creating systemd service..."
sudo sed "s/%i/$CURRENT_USER/g" openirl-discovery.service > /tmp/openirl-discovery.service
sudo mv /tmp/openirl-discovery.service /etc/systemd/system/openirl-discovery.service
sudo chmod 644 /etc/systemd/system/openirl-discovery.service

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Enable and start service
echo "▶️  Enabling and starting service..."
sudo systemctl enable openirl-discovery.service
sudo systemctl start openirl-discovery.service

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Installation complete!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

sleep 2

echo -e "${GREEN}📊 Service status:${NC}"
sudo systemctl status openirl-discovery.service --no-pager | head -10

echo ""
echo -e "${YELLOW}📝 Useful commands:${NC}"
echo "   View logs:      sudo journalctl -u openirl-discovery -f"
echo "   Stop service:   sudo systemctl stop openirl-discovery"
echo "   Start service:  sudo systemctl start openirl-discovery"
echo "   Restart:        sudo systemctl restart openirl-discovery"
echo "   Check status:   sudo systemctl status openirl-discovery"
echo ""
echo -e "${GREEN}✨ New streams will now be automatically discovered and added to:${NC}"
echo "   ~/recordings/stream_ids.txt"
echo ""
