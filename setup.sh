#!/bin/bash

# TravelNet Portal Setup Script
# This script configures a Raspberry Pi as a travel router with web management interface

set -e  # Exit on any error

APP_NAME="TravelNet Portal"
APP_DIR="/opt/travelnet"
SERVICE_NAME="travelnet"
AP_INTERFACE="wlan0"
WIFI_INTERFACE="wlan1"
AP_IP="192.168.4.1"
AP_SUBNET="192.168.4.0/24"
DHCP_RANGE="192.168.4.2,192.168.4.20,255.255.255.0,12h"

echo "========================================="
echo "  $APP_NAME Setup Script"
echo "========================================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 
   exit 1
fi

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "Warning: This script is designed for Raspberry Pi. Continue anyway? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Step 1: Updating system packages..."
apt update && apt upgrade -y

echo "Step 2: Installing required packages..."
# Remove conflicting packages first
apt remove -y iptables-persistent netfilter-persistent 2>/dev/null || true

apt install -y \
    hostapd \
    dnsmasq \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    nginx \
    ufw \
    network-manager \
    rfkill \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    libwebp-dev \
    build-essential

echo "Step 3: Creating application directory..."
mkdir -p $APP_DIR
mkdir -p $APP_DIR/logs
mkdir -p $APP_DIR/vpn_configs

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
chmod +x $APP_DIR/setup.sh

echo "Step 7: Configuring hostapd (Access Point)..."
cat > /etc/hostapd/hostapd.conf << EOF
# Interface configuration
interface=$AP_INTERFACE
driver=nl80211

# Network configuration
ssid=TravelNet-$(hostname)
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0

# Security configuration
wpa=2
wpa_passphrase=TravelNet123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP

# Country code (change as needed)
country_code=US
ieee80211n=1
ieee80211d=1
EOF

echo "Step 8: Configuring dnsmasq (DHCP server)..."
cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup
cat > /etc/dnsmasq.conf << EOF
# Interface configuration
interface=$AP_INTERFACE
bind-interfaces

# DHCP configuration
dhcp-range=$DHCP_RANGE
dhcp-option=3,$AP_IP
dhcp-option=6,$AP_IP

# DNS configuration
server=8.8.8.8
server=8.8.4.4

# Captive portal
address=/#/$AP_IP
EOF

echo "Step 9: Configuring network interfaces..."
cat > /etc/systemd/network/08-$AP_INTERFACE.network << EOF
[Match]
Name=$AP_INTERFACE

[Network]
Address=$AP_IP/24
IPMasquerade=yes
IPForward=yes
EOF

echo "Step 10: Setting up IP forwarding..."
echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf

echo "Step 11: Configuring iptables rules..."
iptables -t nat -A POSTROUTING -o $WIFI_INTERFACE -j MASQUERADE
iptables -A FORWARD -i $WIFI_INTERFACE -o $AP_INTERFACE -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i $AP_INTERFACE -o $WIFI_INTERFACE -j ACCEPT

# Redirect HTTP traffic to captive portal
iptables -t nat -A PREROUTING -i $AP_INTERFACE -p tcp --dport 80 -j DNAT --to-destination $AP_IP:80
iptables -t nat -A PREROUTING -i $AP_INTERFACE -p tcp --dport 443 -j DNAT --to-destination $AP_IP:80

# Configure UFW firewall
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 53
ufw --force enable

echo "Step 12: Creating systemd service..."
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=$APP_NAME
After=network.target

[Service]
Type=simple
User=$SYSTEM_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "Step 13: Configuring nginx reverse proxy..."
cat > /etc/nginx/sites-available/travelnet << EOF
server {
    listen 8080;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/travelnet /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

echo "Step 14: Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow 80/tcp
ufw allow 8080/tcp
ufw allow 53
ufw allow 67/udp

echo "Step 15: Enabling services..."
systemctl daemon-reload
systemctl enable hostapd
systemctl enable dnsmasq
systemctl enable $SERVICE_NAME
systemctl enable nginx
systemctl enable systemd-networkd

echo "Step 16: Configuring NetworkManager..."
cat > /etc/NetworkManager/conf.d/99-unmanaged-devices.conf << EOF
[keyfile]
unmanaged-devices=interface-name:$AP_INTERFACE
EOF

echo "Step 17: Creating startup script..."
cat > $APP_DIR/start.sh << 'EOF'
#!/bin/bash
# TravelNet startup script

# Ensure interfaces are up
ip link set wlan0 up
ip link set wlan1 up

# Start services
systemctl start hostapd
systemctl start dnsmasq
systemctl start travelnet
systemctl start nginx

echo "TravelNet Portal started successfully!"
echo "Access Point: TravelNet-$(hostname)"
echo "Password: TravelNet123"
echo "Portal URL: http://192.168.4.1"
EOF

chmod +x $APP_DIR/start.sh

echo "Step 18: Creating management script..."
cat > $APP_DIR/manage.sh << 'EOF'
#!/bin/bash
# TravelNet management script

case "$1" in
    start)
        sudo systemctl start hostapd dnsmasq travelnet nginx
        echo "TravelNet services started"
        ;;
    stop)
        sudo systemctl stop nginx travelnet dnsmasq hostapd
        echo "TravelNet services stopped"
        ;;
    restart)
        sudo systemctl restart hostapd dnsmasq travelnet nginx
        echo "TravelNet services restarted"
        ;;
    status)
        sudo systemctl status hostapd dnsmasq travelnet nginx
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

echo "Step 19: Creating configuration backup..."
mkdir -p $APP_DIR/backups
cp /etc/hostapd/hostapd.conf $APP_DIR/backups/
cp /etc/dnsmasq.conf $APP_DIR/backups/
cp /etc/systemd/system/$SERVICE_NAME.service $APP_DIR/backups/

echo "Step 20: Final system configuration..."
# Disable WiFi power management
echo 'wireless-power off' >> /etc/NetworkManager/conf.d/default-wifi-powersave-on.conf

# Set hostname if not already set
if [[ $(hostname) == "raspberrypi" ]]; then
    echo "travelnet" > /etc/hostname
    sed -i 's/raspberrypi/travelnet/g' /etc/hosts
fi

echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "Configuration Summary:"
echo "- Access Point Interface: $AP_INTERFACE"
echo "- WiFi Client Interface: $WIFI_INTERFACE"
echo "- Access Point IP: $AP_IP"
echo "- Access Point SSID: TravelNet-$(hostname)"
echo "- Access Point Password: TravelNet123"
echo "- Portal URL: http://$AP_IP"
echo ""
echo "Next Steps:"
echo "1. Reboot the system: sudo reboot"
echo "2. Connect to the TravelNet-$(hostname) WiFi network"
echo "3. Open http://$AP_IP in your browser"
echo "4. Configure your internet connection through the portal"
echo ""
echo "Service Management:"
echo "- Start services: sudo $APP_DIR/manage.sh start"
echo "- Stop services: sudo $APP_DIR/manage.sh stop"
echo "- Restart services: sudo $APP_DIR/manage.sh restart"
echo "- Check status: sudo $APP_DIR/manage.sh status"
echo "- View logs: sudo $APP_DIR/manage.sh logs"
echo ""
echo "Security Notes:"
echo "- Change the default AP password in /etc/hostapd/hostapd.conf"
echo "- Update the SECRET_KEY in config.py for production use"
echo "- SSH is enabled by default - secure it properly"
echo ""

read -p "Would you like to reboot now? (y/N): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Rebooting in 5 seconds..."
    sleep 5
    reboot
fi