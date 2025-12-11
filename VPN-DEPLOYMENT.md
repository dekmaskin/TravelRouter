# VPN Tunnel Deployment Guide

This guide covers deploying the VPN tunnel feature to your Raspberry Pi travel router.

## Overview

The VPN tunnel feature allows your travel router to connect to your home VPN server, routing all traffic through your home internet connection. This provides:

- **Privacy**: Browse the web as if you're at home
- **Security**: Encrypted tunnel through public WiFi
- **Access**: Reach home network resources while traveling
- **Geo-location**: Appear to be browsing from your home location

## Prerequisites

- Raspberry Pi with TravelNet Portal already installed
- SSH access to your Pi (`johan@10.10.10.60`)
- WireGuard configuration file from your home VPN server
- Sudo privileges on the Pi

## Deployment Steps

### 1. Deploy Application Code

First, deploy the updated application code to your Pi:

```bash
# From your development machine
scp -r app/ johan@10.10.10.60:~/travelnet-portal/
scp -r templates/ johan@10.10.10.60:~/travelnet-portal/
scp -r static/ johan@10.10.10.60:~/travelnet-portal/
scp setup-vpn.sh johan@10.10.10.60:~/
```

### 2. Install WireGuard on Pi

SSH to your Pi and run the VPN setup script:

```bash
ssh johan@10.10.10.60
chmod +x setup-vpn.sh
./setup-vpn.sh
```

This script will:
- Install WireGuard and required tools
- Configure proper permissions
- Enable IP forwarding
- Set up firewall rules
- Create VPN configuration directory

### 3. Restart Application

Restart the TravelNet Portal service to load the new VPN functionality:

```bash
# On the Pi
sudo systemctl restart travelnet-portal
# or if running manually:
# cd ~/travelnet-portal && python3 run.py
```

### 4. Verify Installation

Check that the VPN feature is available:

1. Open the web interface: `http://192.168.4.1`
2. Look for the "VPN Tunnel" button on the dashboard
3. Navigate to the VPN management page: `http://192.168.4.1/vpn-tunnel`
4. Verify WireGuard is installed (should show "Installed" status)

## Setting Up Your Home VPN Server

To use this feature, you need a WireGuard server at home. Here are your options:

### Option 1: Router with WireGuard Support

Many modern routers support WireGuard:
- ASUS routers with Merlin firmware
- pfSense/OPNsense
- UniFi Dream Machine
- GL.iNet routers

### Option 2: Dedicated Server/NAS

Set up WireGuard on:
- Synology/QNAP NAS
- Home server running Linux
- Docker container
- Raspberry Pi at home

### Option 3: Cloud VPN Service

Use a WireGuard-compatible VPN service:
- Mullvad VPN
- IVPN
- ProtonVPN
- Surfshark

## WireGuard Configuration

### Sample Home Server Configuration

**Server configuration** (`/etc/wireguard/wg0.conf` on your home server):

```ini
[Interface]
PrivateKey = SERVER_PRIVATE_KEY_HERE
Address = 10.0.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
# TravelNet Portal
PublicKey = TRAVEL_ROUTER_PUBLIC_KEY_HERE
AllowedIPs = 10.0.0.2/32
```

**Client configuration** (for your travel router):

```ini
[Interface]
PrivateKey = TRAVEL_ROUTER_PRIVATE_KEY_HERE
Address = 10.0.0.2/24
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = SERVER_PUBLIC_KEY_HERE
Endpoint = your-home-ip-or-domain.com:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
```

### Generating Keys

Generate WireGuard keys on your home server:

```bash
# Generate private key
wg genkey | tee private.key | wg pubkey > public.key

# For travel router
wg genkey | tee travel-private.key | wg pubkey > travel-public.key
```

## Using the VPN Feature

### Upload Configuration

1. Navigate to `http://192.168.4.1/vpn-tunnel`
2. Click "Upload Config"
3. Enter a name (e.g., "home_server")
4. Paste your WireGuard configuration
5. Click "Upload"

### Connect to VPN

**From Dashboard:**
- Click the "VPN Off/On" toggle button

**From VPN Page:**
- Click "Connect VPN"
- Select your configuration
- Click "Connect"

### Monitor Connection

The interface shows:
- Connection status
- Server endpoint
- Allowed IPs
- Last handshake time
- Data transfer statistics

## Troubleshooting

### Common Issues

**WireGuard not installed:**
```bash
sudo apt update && sudo apt install wireguard wireguard-tools
```

**Permission denied:**
```bash
# Check sudoers rule exists
sudo cat /etc/sudoers.d/travelnet-vpn
```

**Connection fails:**
- Verify endpoint is reachable
- Check firewall on home server (port 51820/udp)
- Verify keys are correct
- Check home server is running

**No internet through VPN:**
- Verify IP forwarding: `cat /proc/sys/net/ipv4/ip_forward` (should be 1)
- Check home server routing/NAT configuration
- Verify DNS settings in config

### Debug Commands

```bash
# Check WireGuard status
sudo wg show

# Check interface status
ip addr show wg0

# Check routing
ip route

# Test connectivity
ping 8.8.8.8
```

### Log Files

Check application logs:
```bash
tail -f ~/travelnet-portal/logs/travelnet.log
```

Check system logs:
```bash
sudo journalctl -u wg-quick@wg0 -f
```

## Security Considerations

1. **Key Management**: Keep private keys secure and never share them
2. **Endpoint Security**: Use strong authentication on your home server
3. **Network Isolation**: Consider isolating VPN traffic from home network
4. **Regular Updates**: Keep WireGuard and system packages updated
5. **Monitoring**: Monitor VPN connections and unusual traffic

## Advanced Configuration

### Split Tunneling

To route only specific traffic through VPN, modify `AllowedIPs`:

```ini
# Route only specific networks
AllowedIPs = 192.168.1.0/24, 10.0.0.0/8

# Route everything except local networks
AllowedIPs = 0.0.0.0/1, 128.0.0.0/1
```

### Multiple Configurations

You can upload multiple VPN configurations:
- Home server
- Cloud VPN service
- Work VPN
- Different geographic locations

### Auto-Connect

The system remembers the last connected configuration and can auto-reconnect on startup.

## Support

For issues with the VPN feature:

1. Check the troubleshooting section above
2. Review application logs
3. Verify WireGuard configuration
4. Test connectivity to VPN server
5. Check firewall settings on both ends

The VPN tunnel feature integrates seamlessly with your travel router, providing secure connectivity wherever you go.