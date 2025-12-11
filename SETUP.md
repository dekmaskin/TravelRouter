# TravelNet Portal Setup Guide

This guide will help you set up TravelNet Portal on your Raspberry Pi in just a few minutes.

## 🚀 Quick Start (Recommended)

### One-Command Installation

```bash
curl -sSL https://raw.githubusercontent.com/dekmaskin/TravelRouter/main/install.sh | sudo bash
```

This will:
- Download the latest version
- Run the secure setup script
- Configure all services automatically
- Set up firewall and security

## 📋 Prerequisites

### Hardware Requirements
- **Raspberry Pi 3B+ or newer** (Pi 4 recommended)
- **16GB+ microSD card** (Class 10 or better)
- **Two WiFi interfaces**: Built-in WiFi + USB WiFi adapter OR Ethernet + WiFi
- **Power supply**: Official Raspberry Pi power adapter recommended

### Software Requirements
- **Raspberry Pi OS** (Bullseye or newer)
- **SSH access** enabled
- **Internet connection** for initial setup

### Network Interface Setup

Before installation, identify your network interfaces:

```bash
# List all network interfaces
ip link show

# Check WiFi interfaces specifically
iwconfig
```

Common configurations:
- `wlan0`: Built-in WiFi (will become Access Point)
- `wlan1`: USB WiFi adapter (will connect to internet)
- `eth0`: Ethernet (alternative to wlan1)

## 🔧 Manual Installation

If you prefer manual control over the installation:

### Step 1: Download the Repository

```bash
git clone https://github.com/dekmaskin/TravelRouter.git
cd TravelRouter
```

### Step 2: Run Setup Script

```bash
chmod +x setup-secure.sh
sudo ./setup-secure.sh
```

### Step 3: Follow Interactive Setup

The script will prompt you for:
- **Access Point Name** (SSID)
- **WiFi Password** (minimum 8 characters)
- **Portal Name** (optional customization)

### Step 4: Reboot

```bash
sudo reboot
```

## 📱 First Use

### Connecting to Your Portal

1. **Find the WiFi Network**: Look for your Access Point name (default: "TravelNet-Portal")
2. **Connect**: Use the password you set during installation
3. **Open Browser**: Navigate to `http://192.168.4.1`
4. **Configure Internet**: Scan and connect to available WiFi networks

### Default Settings

- **Portal URL**: `http://192.168.4.1`
- **Access Point IP**: `192.168.4.1`
- **DHCP Range**: `192.168.4.2` - `192.168.4.20`
- **Default SSID**: `TravelNet-Portal`

## 🛠️ Customization

### Changing Access Point Settings

Edit the configuration file:
```bash
sudo nano /etc/hostapd/hostapd.conf
```

Key settings:
- `ssid=YourNetworkName`
- `wpa_passphrase=YourPassword`
- `channel=7` (change if interference)

### Updating Portal Name

Edit the environment file:
```bash
sudo nano /opt/travelnet/.env.production
```

Change:
```
APP_NAME="Your Custom Portal Name"
```

### Network Interface Configuration

If your interfaces are different, update:
```bash
sudo nano /opt/travelnet/.env.production
```

Modify:
```
WIFI_INTERFACE=wlan1    # Internet connection interface
AP_INTERFACE=wlan0      # Access Point interface
ETH_INTERFACE=eth0      # Ethernet interface (if used)
```

## 🔐 Security Hardening

### Change Default Passwords

1. **WiFi Password**: Update in `/etc/hostapd/hostapd.conf`
2. **SSH Keys**: Set up key-based authentication
3. **System Updates**: Keep packages updated

### SSH Security

```bash
# Generate SSH key pair (on your computer)
ssh-keygen -t ed25519

# Copy to Pi
ssh-copy-id pi@YOUR_PI_IP

# Disable password authentication
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart ssh
```

### Firewall Configuration

The setup script configures UFW automatically, but you can customize:

```bash
# Check current rules
sudo ufw status

# Add custom rules
sudo ufw allow from 192.168.1.0/24 to any port 22  # SSH from home network only
```

## 📊 Management

### Service Control

Use the management script:

```bash
# Start services
sudo /opt/travelnet/manage.sh start

# Stop services  
sudo /opt/travelnet/manage.sh stop

# Restart services
sudo /opt/travelnet/manage.sh restart

# Check status
sudo /opt/travelnet/manage.sh status

# View logs
sudo /opt/travelnet/manage.sh logs
```

### Manual Service Control

```bash
# Individual service control
sudo systemctl start|stop|restart travelnet
sudo systemctl start|stop|restart hostapd
sudo systemctl start|stop|restart dnsmasq

# Check service status
sudo systemctl status travelnet
```

## 🚨 Troubleshooting

### Common Issues

**1. Can't connect to Access Point**
```bash
# Check hostapd status
sudo systemctl status hostapd

# Check interface status
ip addr show wlan0

# Restart hostapd
sudo systemctl restart hostapd
```

**2. No internet after connecting to public WiFi**
```bash
# Check client interface
nmcli device status

# Check IP forwarding
cat /proc/sys/net/ipv4/ip_forward

# Check iptables rules
sudo iptables -L -n
```

**3. Portal not accessible**
```bash
# Check TravelNet service
sudo systemctl status travelnet

# Check logs
sudo journalctl -u travelnet -f

# Restart service
sudo systemctl restart travelnet
```

### Getting Help

1. **Check logs**: `sudo /opt/travelnet/manage.sh logs`
2. **System logs**: `sudo journalctl -u travelnet -f`
3. **Network status**: `nmcli device status`
4. **Interface status**: `ip addr show`

### Reset to Defaults

If you need to start over:

```bash
# Stop services
sudo systemctl stop travelnet hostapd dnsmasq

# Remove configuration
sudo rm -rf /opt/travelnet
sudo rm /etc/hostapd/hostapd.conf
sudo rm /etc/systemd/system/travelnet.service

# Re-run setup
sudo ./setup-secure.sh
```

## 🔄 Updates

### Updating TravelNet Portal

```bash
# Backup current installation
sudo cp -r /opt/travelnet /opt/travelnet.backup.$(date +%Y%m%d)

# Download updates
cd /tmp
git clone https://github.com/USERNAME/REPOSITORY.git
cd REPOSITORY

# Copy new files
sudo cp -r app/ /opt/travelnet/
sudo cp -r templates/ /opt/travelnet/
sudo cp -r static/ /opt/travelnet/

# Update dependencies
cd /opt/travelnet
source venv/bin/activate
sudo pip install -r requirements.txt

# Restart services
sudo systemctl restart travelnet
```

### System Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Reboot if kernel was updated
sudo reboot
```

## 📞 Support

- **Documentation**: Check README.md and other .md files
- **Issues**: Report bugs on GitHub
- **Community**: Join discussions for help and tips

---

**Next Steps**: After setup, explore the [VPN features](VPN-DEPLOYMENT.md) and [security options](SECURITY.md).