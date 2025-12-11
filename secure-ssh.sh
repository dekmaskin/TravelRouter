#!/bin/bash

# Secure SSH Configuration Script
# Restricts SSH access to ethernet interface only

set -e

echo "========================================="
echo "  SSH Security Configuration"
echo "========================================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 
   exit 1
fi

# Get ethernet IP address
ETH_IP=$(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1)

if [[ -z "$ETH_IP" ]]; then
    echo "Error: Could not determine ethernet IP address"
    echo "Make sure ethernet interface (eth0) is connected and has an IP"
    exit 1
fi

echo "Detected ethernet IP: $ETH_IP"
echo ""

# Backup current SSH config
echo "Step 1: Backing up SSH configuration..."
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d-%H%M%S)
echo "✓ SSH config backed up"

# Create new SSH configuration
echo "Step 2: Configuring SSH to listen only on ethernet interface..."

# Remove any existing ListenAddress lines
sed -i '/^ListenAddress/d' /etc/ssh/sshd_config
sed -i '/^#ListenAddress/d' /etc/ssh/sshd_config

# Add our secure ListenAddress configuration
cat >> /etc/ssh/sshd_config << EOF

# TravelNet Security Configuration
# SSH only accessible via ethernet interface
ListenAddress $ETH_IP
Port 22

# Additional security settings
PermitRootLogin no
PasswordAuthentication yes
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
MaxAuthTries 3
MaxSessions 2
ClientAliveInterval 300
ClientAliveCountMax 2

# Disable X11 forwarding for security
X11Forwarding no

# Only allow specific users (add more as needed)
AllowUsers johan

EOF

echo "✓ SSH configuration updated"

# Test SSH configuration
echo "Step 3: Testing SSH configuration..."
if sshd -t; then
    echo "✓ SSH configuration is valid"
else
    echo "✗ SSH configuration has errors!"
    echo "Restoring backup..."
    cp /etc/ssh/sshd_config.backup.* /etc/ssh/sshd_config
    exit 1
fi

# Restart SSH service
echo "Step 4: Restarting SSH service..."
systemctl restart ssh

if systemctl is-active --quiet ssh; then
    echo "✓ SSH service restarted successfully"
else
    echo "✗ SSH service failed to start!"
    echo "Restoring backup..."
    cp /etc/ssh/sshd_config.backup.* /etc/ssh/sshd_config
    systemctl restart ssh
    exit 1
fi

echo ""
echo "========================================="
echo "  SSH Security Configuration Complete!"
echo "========================================="
echo ""
echo "SSH is now ONLY accessible via:"
echo "  - Ethernet IP: $ETH_IP"
echo "  - Port: 22"
echo ""
echo "SSH is NO LONGER accessible via:"
echo "  - WiFi client IP (wlan1)"
echo "  - Hotspot IP (wlan0)"
echo "  - VPN IP (wg0)"
echo ""
echo "Security improvements applied:"
echo "  ✓ SSH restricted to ethernet interface only"
echo "  ✓ Root login disabled"
echo "  ✓ Maximum 3 authentication attempts"
echo "  ✓ Maximum 2 concurrent sessions"
echo "  ✓ Client timeout after 5 minutes of inactivity"
echo "  ✓ X11 forwarding disabled"
echo "  ✓ Only 'johan' user allowed"
echo ""
echo "To connect via SSH:"
echo "  ssh johan@$ETH_IP"
echo ""
echo "To restore previous configuration:"
echo "  sudo cp /etc/ssh/sshd_config.backup.* /etc/ssh/sshd_config"
echo "  sudo systemctl restart ssh"
echo ""