#!/bin/bash

# TravelNet Portal VPN Setup Script
# This script installs and configures WireGuard for VPN tunnel functionality
# 
# IMPORTANT: This script should be run on the Raspberry Pi, not the development machine
# 
# To deploy to your Pi:
# 1. Copy this script to your Pi: scp setup-vpn.sh pi@YOUR_PI_IP:~/
# 2. SSH to your Pi: ssh pi@YOUR_PI_IP
# 3. Run the script: chmod +x setup-vpn.sh && ./setup-vpn.sh

set -e

echo "=========================================="
echo "TravelNet Portal VPN Setup (Raspberry Pi)"
echo "=========================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root for security reasons."
   echo "Please run as a regular user with sudo privileges."
   exit 1
fi

# Check for sudo privileges
if ! sudo -n true 2>/dev/null; then
    echo "This script requires sudo privileges. Please ensure you can run sudo commands."
    exit 1
fi

echo "Step 1: Updating package lists..."
sudo apt update

echo "Step 2: Installing WireGuard..."
if ! command -v wg &> /dev/null; then
    sudo apt install -y wireguard wireguard-tools
    echo "✓ WireGuard installed successfully"
else
    echo "✓ WireGuard is already installed"
fi

echo "Step 3: Installing additional networking tools..."
sudo apt install -y resolvconf

echo "Step 4: Setting up WireGuard permissions..."
# Ensure the user can manage WireGuard interfaces
sudo usermod -a -G sudo $USER

# Create sudoers rule for WireGuard commands (more secure than full sudo)
SUDOERS_FILE="/etc/sudoers.d/travelnet-vpn"
if [ ! -f "$SUDOERS_FILE" ]; then
    echo "Creating sudoers rule for VPN management..."
    sudo tee "$SUDOERS_FILE" > /dev/null << EOF
# TravelNet Portal VPN Management
# Allow the application user to manage WireGuard interfaces
$USER ALL=(ALL) NOPASSWD: /usr/bin/wg, /usr/bin/wg-quick
EOF
    sudo chmod 440 "$SUDOERS_FILE"
    echo "✓ Sudoers rule created for VPN management"
else
    echo "✓ Sudoers rule already exists"
fi

echo "Step 5: Enabling IP forwarding..."
# Enable IP forwarding for VPN routing
if ! grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf; then
    echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
    sudo sysctl -p
    echo "✓ IP forwarding enabled"
else
    echo "✓ IP forwarding already enabled"
fi

echo "Step 6: Setting up firewall rules..."
# Configure UFW for VPN traffic
sudo ufw --force enable

# Allow VPN traffic
sudo ufw allow 51820/udp comment "WireGuard VPN"

# Allow forwarding for VPN
if ! sudo ufw status | grep -q "51820/udp"; then
    sudo ufw reload
fi

echo "Step 7: Creating VPN configuration directory..."
VPN_CONFIG_DIR="./vpn_configs"
if [ ! -d "$VPN_CONFIG_DIR" ]; then
    mkdir -p "$VPN_CONFIG_DIR"
    chmod 700 "$VPN_CONFIG_DIR"
    echo "✓ VPN configuration directory created"
else
    echo "✓ VPN configuration directory already exists"
fi

echo "Step 8: Verifying installation..."
if command -v wg &> /dev/null && command -v wg-quick &> /dev/null; then
    echo "✓ WireGuard installation verified"
    wg --version
else
    echo "✗ WireGuard installation failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "VPN Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Obtain a WireGuard configuration file from your VPN provider or home server"
echo "2. Upload the configuration through the TravelNet Portal web interface"
echo "3. Connect to your VPN tunnel from the dashboard"
echo ""
echo "Example WireGuard configuration format:"
echo ""
echo "[Interface]"
echo "PrivateKey = YOUR_PRIVATE_KEY_HERE"
echo "Address = 10.0.0.2/24"
echo "DNS = 1.1.1.1, 8.8.8.8"
echo ""
echo "[Peer]"
echo "PublicKey = SERVER_PUBLIC_KEY_HERE"
echo "Endpoint = your.server.com:51820"
echo "AllowedIPs = 0.0.0.0/0"
echo ""
echo "For security, configuration files are stored in: $VPN_CONFIG_DIR"
echo "Make sure to keep your private keys secure!"
echo ""
echo "You can now access the VPN management interface at:"
echo "http://192.168.4.1/vpn-tunnel"
echo ""