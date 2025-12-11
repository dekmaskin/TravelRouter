# Deployment Guide

This guide covers secure deployment of TravelNet Portal in production environments.

## 🚀 Production Deployment

### System Requirements

**Minimum Requirements:**
- Raspberry Pi 3B+ or newer
- 16GB microSD card (Class 10 or better)
- 2 WiFi interfaces (built-in + USB adapter) OR Ethernet + WiFi
- 1GB RAM (2GB+ recommended)

**Recommended Setup:**
- Raspberry Pi 4B with 4GB RAM
- 32GB microSD card (SanDisk Extreme or similar)
- High-quality USB WiFi adapter (AC600 or better)
- Proper cooling (heatsinks/fan)

### Pre-Deployment Checklist

- [ ] Fresh Raspberry Pi OS installation
- [ ] SSH access configured
- [ ] System packages updated
- [ ] Network interfaces identified
- [ ] Backup strategy planned

## 🔧 Installation Methods

### Method 1: Automated Setup (Recommended)

```bash
# Download and run the secure setup script
curl -sSL https://raw.githubusercontent.com/your-repo/travelnet-portal/main/setup-secure.sh | sudo bash
```

### Method 2: Manual Installation

1. **Clone Repository:**
   ```bash
   git clone https://github.com/your-repo/travelnet-portal.git
   cd travelnet-portal
   ```

2. **Run Setup Script:**
   ```bash
   chmod +x setup-secure.sh
   sudo ./setup-secure.sh
   ```

3. **Follow Interactive Prompts:**
   - Enter custom SSID (or use default)
   - Set secure password (minimum 8 characters)
   - Confirm network interfaces

### Method 3: Docker Deployment

```bash
# Build the container
docker build -t travelnet-portal .

# Run with proper network configuration
docker run -d \
  --name travelnet \
  --network host \
  --privileged \
  -v /opt/travelnet/logs:/app/logs \
  -e SECRET_KEY="your-secret-key" \
  travelnet-portal
```

## ⚙️ Configuration

### Environment Configuration

Create `/opt/travelnet/.env.production`:

```bash
# Security (REQUIRED)
SECRET_KEY=your-secure-secret-key-here
APP_NAME="Your Portal Name"

# Network Configuration
WIFI_INTERFACE=wlan1
AP_INTERFACE=wlan0
ETH_INTERFACE=eth0

# Access Point Settings
DEFAULT_AP_SSID="Your-Network-Name"
DEFAULT_AP_PASSWORD="Your-Secure-Password"

# Security Settings
MAX_REQUESTS_PER_MINUTE=60
MAX_CONNECTION_ATTEMPTS=5

# Feature Toggles
ENABLE_SSH_MANAGEMENT=true
ENABLE_SYSTEM_REBOOT=true
ENABLE_QR_GENERATION=true

# Production Settings
DEBUG=false
TESTING=false
LOG_LEVEL=INFO
```

### Network Interface Configuration

Identify your network interfaces:
```bash
# List all network interfaces
ip link show

# Check WiFi interfaces
iwconfig

# Test interface capabilities
iw list
```

Common interface names:
- `wlan0`: Built-in WiFi (usually used for AP)
- `wlan1`: USB WiFi adapter (usually used for client)
- `eth0`: Ethernet interface

### Firewall Configuration

The setup script configures UFW automatically, but you can customize:

```bash
# Check current rules
sudo ufw status verbose

# Add custom rules
sudo ufw allow from 192.168.1.0/24 to any port 22  # SSH from local network only
sudo ufw allow 8080/tcp  # Alternative web port

# Remove rules
sudo ufw delete allow 80/tcp
```

## 🔐 Security Hardening

### SSH Security

1. **Generate SSH Keys:**
   ```bash
   ssh-keygen -t ed25519 -C "your-email@example.com"
   ssh-copy-id user@your-pi-ip
   ```

2. **Harden SSH Configuration:**
   ```bash
   sudo nano /etc/ssh/sshd_config
   ```
   
   Add/modify:
   ```
   PermitRootLogin no
   PasswordAuthentication no
   PubkeyAuthentication yes
   MaxAuthTries 3
   ClientAliveInterval 300
   ClientAliveCountMax 2
   AllowUsers your-username
   ```

3. **Restart SSH:**
   ```bash
   sudo systemctl restart ssh
   ```

### System Security

1. **Enable Automatic Updates:**
   ```bash
   sudo apt install unattended-upgrades
   sudo dpkg-reconfigure -plow unattended-upgrades
   ```

2. **Configure Fail2ban:**
   ```bash
   sudo nano /etc/fail2ban/jail.local
   ```
   
   Add:
   ```ini
   [DEFAULT]
   bantime = 3600
   findtime = 600
   maxretry = 5
   
   [sshd]
   enabled = true
   maxretry = 3
   
   [nginx-http-auth]
   enabled = true
   ```

3. **Set Up Log Monitoring:**
   ```bash
   # Install logwatch
   sudo apt install logwatch
   
   # Configure daily reports
   sudo nano /etc/cron.daily/00logwatch
   ```

## 📊 Monitoring & Maintenance

### Service Management

Use the included management script:

```bash
# Start all services
/opt/travelnet/manage.sh start

# Stop all services
/opt/travelnet/manage.sh stop

# Restart services
/opt/travelnet/manage.sh restart

# Check status
/opt/travelnet/manage.sh status

# View logs
/opt/travelnet/manage.sh logs
```

### Health Monitoring

Create a health check script:

```bash
#!/bin/bash
# /opt/travelnet/health-check.sh

# Check if services are running
systemctl is-active --quiet travelnet || echo "TravelNet service down"
systemctl is-active --quiet hostapd || echo "HostAPD service down"
systemctl is-active --quiet dnsmasq || echo "DNSMasq service down"

# Check disk space
df -h | awk '$5 > 80 {print "Disk space warning: " $0}'

# Check memory usage
free | awk 'NR==2{printf "Memory usage: %.2f%%\n", $3*100/$2}'

# Check network interfaces
ip link show wlan0 | grep -q "state UP" || echo "AP interface down"
ip link show wlan1 | grep -q "state UP" || echo "Client interface down"
```

### Log Management

Configure log rotation:

```bash
# /etc/logrotate.d/travelnet
/opt/travelnet/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
    su travelnet travelnet
}
```

## 🔄 Updates & Maintenance

### Application Updates

```bash
# Backup current installation
sudo cp -r /opt/travelnet /opt/travelnet.backup.$(date +%Y%m%d)

# Pull latest changes
cd /opt/travelnet
sudo git pull origin main

# Update dependencies
source venv/bin/activate
sudo pip install -r requirements.txt

# Restart services
sudo systemctl restart travelnet
```

### System Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
source /opt/travelnet/venv/bin/activate
pip list --outdated
pip install --upgrade package-name

# Reboot if kernel updated
sudo reboot
```

## 🚨 Troubleshooting

### Common Issues

1. **Services Won't Start:**
   ```bash
   # Check service status
   sudo systemctl status travelnet hostapd dnsmasq
   
   # Check logs
   sudo journalctl -u travelnet -f
   sudo journalctl -u hostapd -f
   ```

2. **No Internet Access:**
   ```bash
   # Check IP forwarding
   cat /proc/sys/net/ipv4/ip_forward
   
   # Check iptables rules
   sudo iptables -L -n
   sudo iptables -t nat -L -n
   ```

3. **Can't Connect to AP:**
   ```bash
   # Check hostapd configuration
   sudo hostapd -d /etc/hostapd/hostapd.conf
   
   # Check interface status
   ip addr show wlan0
   ```

### Performance Optimization

1. **Optimize WiFi Settings:**
   ```bash
   # Disable power management
   sudo iwconfig wlan1 power off
   
   # Set optimal channel
   sudo iwconfig wlan0 channel 6
   ```

2. **System Performance:**
   ```bash
   # Increase swap if needed
   sudo dphys-swapfile swapoff
   sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=1024
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```

## 📋 Backup & Recovery

### Backup Strategy

1. **Configuration Backup:**
   ```bash
   # Create backup script
   #!/bin/bash
   BACKUP_DIR="/home/pi/backups/$(date +%Y%m%d)"
   mkdir -p $BACKUP_DIR
   
   # Backup configuration files
   cp /etc/hostapd/hostapd.conf $BACKUP_DIR/
   cp /etc/dnsmasq.conf $BACKUP_DIR/
   cp /opt/travelnet/.env.production $BACKUP_DIR/
   cp -r /opt/travelnet/backups/* $BACKUP_DIR/
   
   # Create archive
   tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
   rm -rf $BACKUP_DIR
   ```

2. **Full System Backup:**
   ```bash
   # Create SD card image
   sudo dd if=/dev/mmcblk0 of=/path/to/backup.img bs=4M status=progress
   
   # Compress image
   gzip /path/to/backup.img
   ```

### Recovery Procedures

1. **Configuration Recovery:**
   ```bash
   # Restore from backup
   tar -xzf backup.tar.gz
   sudo cp backup/* /etc/hostapd/
   sudo cp backup/.env.production /opt/travelnet/
   sudo systemctl restart travelnet hostapd dnsmasq
   ```

2. **Full System Recovery:**
   ```bash
   # Flash backup image to new SD card
   sudo dd if=backup.img.gz of=/dev/sdX bs=4M status=progress
   ```

## 📞 Support

### Getting Help

1. **Check Documentation:**
   - README.md - Basic setup and usage
   - SECURITY.md - Security best practices
   - This file - Deployment guide

2. **Log Analysis:**
   ```bash
   # Application logs
   tail -f /opt/travelnet/logs/travelnet.log
   
   # System logs
   sudo journalctl -u travelnet -f
   sudo journalctl -u hostapd -f
   sudo journalctl -u dnsmasq -f
   ```

3. **Community Support:**
   - GitHub Issues: Report bugs and feature requests
   - Discussions: Ask questions and share experiences
   - Wiki: Community-contributed guides and tips

### Professional Support

For enterprise deployments or professional support:
- Email: support@your-domain.com
- Response time: 24-48 hours
- Available services: Custom deployment, training, maintenance contracts

---

**Next Steps:** After deployment, review the [SECURITY.md](SECURITY.md) file for additional security hardening recommendations.