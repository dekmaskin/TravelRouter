#!/bin/bash

# Firewall Setup Script for TravelNet Router
# Adds iptables rules to secure SSH access

set -e

echo "========================================="
echo "  TravelNet Firewall Setup"
echo "========================================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 
   exit 1
fi

# Install iptables-persistent if not already installed
echo "Step 1: Installing iptables-persistent..."
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y iptables-persistent

# Get interface IPs
ETH_IP=$(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1)
HOTSPOT_IP=$(ip -4 addr show wlan0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1)

echo "Detected IPs:"
echo "  Ethernet (eth0): $ETH_IP"
echo "  Hotspot (wlan0): $HOTSPOT_IP"
echo ""

# Backup existing rules
echo "Step 2: Backing up existing firewall rules..."
iptables-save > /etc/iptables/rules.backup.$(date +%Y%m%d-%H%M%S)
echo "✓ Firewall rules backed up"

# Clear existing rules
echo "Step 3: Setting up firewall rules..."
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

# Default policies
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established and related connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow SSH ONLY on ethernet interface
iptables -A INPUT -i eth0 -p tcp --dport 22 -j ACCEPT

# BLOCK SSH on all other interfaces
iptables -A INPUT -i wlan0 -p tcp --dport 22 -j DROP
iptables -A INPUT -i wlan1 -p tcp --dport 22 -j DROP
iptables -A INPUT -i wg0 -p tcp --dport 22 -j DROP

# Allow HTTP/HTTPS on hotspot interface (for web portal)
iptables -A INPUT -i wlan0 -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -i wlan0 -p tcp --dport 443 -j ACCEPT

# Allow DHCP on hotspot interface
iptables -A INPUT -i wlan0 -p udp --dport 67 -j ACCEPT
iptables -A INPUT -i wlan0 -p udp --dport 68 -j ACCEPT

# Allow DNS on hotspot interface
iptables -A INPUT -i wlan0 -p udp --dport 53 -j ACCEPT
iptables -A INPUT -i wlan0 -p tcp --dport 53 -j ACCEPT

# Allow ping (ICMP)
iptables -A INPUT -p icmp --icmp-type echo-request -j ACCEPT

# NAT rules for internet sharing
iptables -t nat -A POSTROUTING -o wlan1 -j MASQUERADE
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
iptables -A FORWARD -i wlan0 -o wlan1 -j ACCEPT
iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT
iptables -A FORWARD -i wlan1 -o wlan0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i eth0 -o wlan0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Save rules
echo "Step 4: Saving firewall rules..."
iptables-save > /etc/iptables/rules.v4

# Enable IP forwarding
echo "Step 5: Enabling IP forwarding..."
echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf
sysctl -p

echo "✓ Firewall configuration complete"

echo ""
echo "========================================="
echo "  Firewall Rules Applied!"
echo "========================================="
echo ""
echo "SSH Access:"
echo "  ✓ ALLOWED on ethernet (eth0): $ETH_IP:22"
echo "  ✗ BLOCKED on hotspot (wlan0)"
echo "  ✗ BLOCKED on WiFi client (wlan1)"
echo "  ✗ BLOCKED on VPN (wg0)"
echo ""
echo "Web Portal Access:"
echo "  ✓ ALLOWED on hotspot (wlan0): $HOTSPOT_IP:80"
echo ""
echo "Other Services:"
echo "  ✓ DHCP, DNS allowed on hotspot"
echo "  ✓ Internet sharing enabled"
echo "  ✓ Ping allowed"
echo ""
echo "To view current rules:"
echo "  sudo iptables -L -n -v"
echo ""
echo "To restore backup:"
echo "  sudo iptables-restore < /etc/iptables/rules.backup.*"
echo ""