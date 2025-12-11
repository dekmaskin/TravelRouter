#!/bin/bash

# TravelNet Portal Secure Setup Script
# Production-ready setup with security best practices

set -e  # Exit on any error

APP_NAME="${APP_NAME:-TravelNet Portal}"
APP_DIR="/opt/travelnet"
SERVICE_NAME="travelnet"
AP_INTERFACE="wlan0"
WIFI_INTERFACE="wlan1"
AP_IP="192.168.4.1"
AP_SUBNET="192.168.4.0/24"
DHCP_RANGE="192.168.4.2,192.168.4.20,255.255.255.0,12h"

# Default credentials (should be changed after setup)
DEFAULT_AP_SSID="TravelNet-Portal"
DEFAULT_AP_PASSWORD="TravelNet2024!"

echo "========================================="
echo "  $APP_NAME Secure Setup Script"
echo "========================================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 
   exit 1
fi

# Get system user (the user who ran sudo)
SYSTEM_USER="${SUDO_USER:-$USER}"
if [[ "$SYSTEM_USER" == "root" ]]; then
    echo "Please run this script with sudo from a regular user account"
    exit 1
fi

echo "Setting up TravelNet Portal for user: $SYSTEM_USER"
echo ""

# Prompt for custom settings
read -p "Enter Access Point SSID [$DEFAULT_AP_SSID]: " CUSTOM_SSID
AP_SSID="${CUSTOM_SSID:-$DEFAULT_AP_SSID}"

read -s -p "Enter Access Point Password [$DEFAULT_AP_PASSWORD]: " CUSTOM_PASSWORD
echo ""
AP_PASSWORD="${CUSTOM_PASSWORD:-$DEFAULT_AP_PASSWORD}"

# Validate password strength
if [[ ${#AP_PASSWORD} -lt 8 ]]; then
    echo "Error: Password must be at least 8 characters long"
    exit 1
fi

echo "Step 1: Updating system packages..."
apt update && apt upgrade -y

echo "Step 2: Installing required packages..."
apt install -y \
    hostapd \
    dnsmasq \
    iptables-persistent \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nginx \
    ufw \
    network-manager \
    rfkill \
    fail2ban

echo "Step 3: Creating application directory..."
mkdir -p $APP_DIR
mkdir -p $APP_DIR/logs
mkdir -p $APP_DIR/backups

echo "Step 4: Setting up Python virtual environment..."
python3 -m venv $APP_DIR/venv
source $APP_DIR/venv/bin/activate

echo "Step 5: Installing Python dependencies..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    pip install Flask==2.3.3 qrcode[pil]==7.4.2 Werkzeug==2.3.7
fi

echo "Step 6: Copying application files..."
cp -r . $APP_DIR/
chown -R $SYSTEM_USER:$SYSTEM_USER $APP_DIR
chmod +x $APP_DIR/setup-secure.sh

echo "Step 7: Generating secure configuration..."
# Generate a secure secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Get app name from user or use default
if [[ -z "$APP_NAME" ]]; then
    read -p "Enter Portal Name [TravelNet Portal]: " CUSTOM_APP_NAME
    APP_NAME="${CUSTOM_APP_NAME:-TravelNet Portal}"
fi

# Create secure environment file
cat > $APP_DIR/.env.production << EOF
# TravelNet Portal Production Configuration
# Generated on $(date)
SECRET_KEY=$SECRET_KEY
APP_NAME=$APP_NAME
LOG_LEVEL=INFO
WIFI_INTERFACE=$WIFI_INTERFACE
AP_INTERFACE=$AP_INTERFACE
ETH_INTERFACE=eth0
DEFAULT_AP_SSID=$AP_SSID
DEFAULT_AP_PASSWORD=$AP_PASSWORD
DEBUG=false
TESTING=false
ENABLE_SSH_MANAGEMENT=true
ENABLE_SYSTEM_REBOOT=true
ENABLE_QR_GENERATION=true
MAX_REQUESTS_PER_MINUTE=60
MAX_CONNECTION_ATTEMPTS=5
EOF

echo "Step 8: Configuring hostapd (Access Point)..."
cat > /etc/hostapd/hostapd.conf << EOF
# TravelNet Portal Access Point Configuration
interface=$AP_INTERFACE
driver=nl80211

# Network configuration
ssid=$AP_SSID
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0

# Security configuration
wpa=2
wpa_passphrase=$AP_PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP

# Country code (change as needed)
country_code=US
ieee80211n=1
ieee80211d=1

# Security enhancements
max_num_sta=10
EOF

echo "Step 9: Configuring dnsmasq (DHCP server)..."
cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup
cat > /etc/dnsmasq.conf << EOF
# TravelNet Portal DHCP Configuration
interface=$AP_INTERFACE
bind-interfaces

# DHCP configuration
dhcp-range=$DHCP_RANGE
dhcp-option=3,$AP_IP
dhcp-option=6,$AP_IP

# DNS configuration
server=1.1.1.1
server=1.0.0.1
server=8.8.8.8
server=8.8.4.4

# Captive portal
address=/#/$AP_IP

# Security
dhcp-authoritative
EOF

echo "Step 10: Configuring network interfaces..."
cat > /etc/systemd/network/08-$AP_INTERFACE.network << EOF
[Match]
Name=$AP_INTERFACE

[Network]
Address=$AP_IP/24
IPMasquerade=yes
IPForward=yes
EOF

echo "Step 11: Setting up IP forwarding..."
echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf

echo "Step 12: Configuring secure iptables rules..."
# Clear existing rules
iptables -F
iptables -t nat -F

# Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH (be careful with this)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP on AP interface
iptables -A INPUT -i $AP_INTERFACE -p tcp --dport 80 -j ACCEPT

# Allow DHCP and DNS on AP interface
iptables -A INPUT -i $AP_INTERFACE -p udp --dport 67 -j ACCEPT
iptables -A INPUT -i $AP_INTERFACE -p udp --dport 53 -j ACCEPT
iptables -A INPUT -i $AP_INTERFACE -p tcp --dport 53 -j ACCEPT

# NAT rules for internet sharing
iptables -t nat -A POSTROUTING -o $WIFI_INTERFACE -j MASQUERADE
iptables -A FORWARD -i $WIFI_INTERFACE -o $AP_INTERFACE -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i $AP_INTERFACE -o $WIFI_INTERFACE -j ACCEPT

# Captive portal redirects
iptables -t nat -A PREROUTING -i $AP_INTERFACE -p tcp --dport 80 -j DNAT --to-destination $AP_IP:80
iptables -t nat -A PREROUTING -i $AP_INTERFACE -p tcp --dport 443 -j DNAT --to-destination $AP_IP:80

# Save iptables rules
netfilter-persistent save

echo "Step 13: Creating systemd service..."
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=TravelNet Portal Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SYSTEM_USER
Group=$SYSTEM_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env.production
ExecStart=$APP_DIR/venv/bin/python app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR/logs

[Install]
WantedBy=multi-user.target
EOF

echo "Step 14: Configuring fail2ban for security..."
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3
EOF

echo "Step 15: Configuring firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 53
ufw allow 67/udp

echo "Step 16: Enabling services..."
systemctl daemon-reload
systemctl enable hostapd
systemctl enable dnsmasq
systemctl enable $SERVICE_NAME
systemctl enable fail2ban
systemctl enable systemd-networkd

echo "Step 17: Configuring NetworkManager..."
cat > /etc/NetworkManager/conf.d/99-unmanaged-devices.conf << EOF
[keyfile]
unmanaged-devices=interface-name:$AP_INTERFACE
EOF

echo "Step 18: Creating management scripts..."
cat > $APP_DIR/manage.sh << 'EOF'
#!/bin/bash
# TravelNet management script

case "$1" in
    start)
        sudo systemctl start hostapd dnsmasq travelnet
        echo "TravelNet services started"
        ;;
    stop)
        sudo systemctl stop travelnet dnsmasq hostapd
        echo "TravelNet services stopped"
        ;;
    restart)
        sudo systemctl restart hostapd dnsmasq travelnet
        echo "TravelNet services restarted"
        ;;
    status)
        sudo systemctl status hostapd dnsmasq travelnet
        ;;
    logs)
        sudo journalctl -u travelnet -f
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
EOF

chmod +x $APP_DIR/manage.sh

echo "Step 19: Creating backup of configuration..."
mkdir -p $APP_DIR/backups
cp /etc/hostapd/hostapd.conf $APP_DIR/backups/
cp /etc/dnsmasq.conf $APP_DIR/backups/
cp /etc/systemd/system/$SERVICE_NAME.service $APP_DIR/backups/
cp $APP_DIR/.env.production $APP_DIR/backups/

echo "Step 20: Final security hardening..."
# Disable WiFi power management
echo 'wireless-power off' >> /etc/NetworkManager/conf.d/default-wifi-powersave-on.conf

# Set secure permissions
chmod 600 $APP_DIR/.env.production
chmod 600 /etc/hostapd/hostapd.conf

# Create log rotation
cat > /etc/logrotate.d/travelnet << EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF

echo ""
echo "========================================="
echo "  Secure Setup Complete!"
echo "========================================="
echo ""
echo "Configuration Summary:"
echo "- Portal Name: $APP_NAME"
echo "- Access Point SSID: $AP_SSID"
echo "- Access Point IP: $AP_IP"
echo "- Portal URL: http://$AP_IP"
echo "- Application Directory: $APP_DIR"
echo ""
echo "Security Features Enabled:"
echo "- Secure secret key generated"
echo "- Firewall configured"
echo "- Fail2ban enabled"
echo "- Rate limiting enabled"
echo "- Input validation enabled"
echo "- Secure file permissions"
echo ""
echo "Management Commands:"
echo "- Start services: $APP_DIR/manage.sh start"
echo "- Stop services: $APP_DIR/manage.sh stop"
echo "- Restart services: $APP_DIR/manage.sh restart"
echo "- Check status: $APP_DIR/manage.sh status"
echo "- View logs: $APP_DIR/manage.sh logs"
echo ""
echo "IMPORTANT SECURITY NOTES:"
echo "1. Change SSH keys and disable password authentication"
echo "2. Regularly update the system: apt update && apt upgrade"
echo "3. Monitor logs: $APP_DIR/manage.sh logs"
echo "4. Backup configuration files in $APP_DIR/backups/"
echo "5. The WiFi password is: $AP_PASSWORD"
echo ""

read -p "Would you like to reboot now to complete setup? (y/N): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Rebooting in 5 seconds..."
    sleep 5
    reboot
fi

echo "Setup complete! Please reboot manually when ready."