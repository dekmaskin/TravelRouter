# TravelRouter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.3+-green.svg)](https://flask.palletsprojects.com/)

A professional, secure travel router management application that transforms your Raspberry Pi into a powerful WiFi bridge with an intuitive web interface. Perfect for travelers, digital nomads, and anyone needing reliable internet connectivity on the go.

## 🌟 Key Features

- **🔐 Security-First Design**: Rate limiting, input validation, secure session management
- **📱 Mobile-Optimized Interface**: Responsive design that works perfectly on all devices  
- **🌐 WiFi Bridge Functionality**: Connect to public WiFi and share via your own access point
- **🛡️ VPN Tunnel Support**: Route traffic through your home VPN server using WireGuard
- **📊 Real-Time Monitoring**: Live connection status and network diagnostics
- **🔧 System Management**: Remote reboot, SSH control, and service management
- **📱 QR Code Generation & Scanning**: Create and scan QR codes for easy WiFi sharing
- **🛡️ Production Ready**: Comprehensive logging, error handling, and security features

## 🚀 Quick Start

### Prerequisites
- Raspberry Pi 3B+ or newer
- Raspberry Pi OS (Bullseye or newer)
- Two WiFi interfaces (built-in + USB adapter) OR Ethernet + WiFi
- SSH access to your Raspberry Pi

### One-Command Installation
```bash
# Download and run the installer
curl -sSL https://raw.githubusercontent.com/dekmaskin/TravelRouter/main/install.sh | sudo bash
```

### Manual Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/USERNAME/REPOSITORY.git
   cd REPOSITORY
   ```

2. **Run the secure setup:**
   ```bash
   chmod +x setup-secure.sh
   sudo ./setup-secure.sh
   ```

3. **Access your portal:**
   - Connect to your WiFi network (name set during installation)
   - Open `http://192.168.4.1` in your browser
   - Configure your internet connection

📖 **Detailed Setup Guide**: See [SETUP.md](SETUP.md) for complete installation instructions.

## 📱 QR Code Features

### Generate QR Codes
- Create QR codes for any WiFi network
- Support for WPA/WPA2, WEP, and open networks
- Download or print QR codes for easy sharing

### Scan QR Codes
- **Camera Scanning**: Use your device's camera to scan WiFi QR codes
- **File Upload**: Upload QR code images from your device
- **Auto-Connect**: Automatically connect to scanned networks
- **Cross-Platform**: Works on phones, tablets, and computers

**Supported QR Code Format**: Standard WiFi QR codes (`WIFI:T:WPA;S:NetworkName;P:Password;;`)

## 🏗️ Architecture

TravelNet Portal v2.0 features a modern, enterprise-grade modular architecture:

```
travelnet-portal/
├── run.py                   # Application entry point
├── app/                     # Main application package
│   ├── __init__.py         # Application factory
│   ├── core/               # Core functionality
│   │   ├── config.py       # Configuration management
│   │   ├── security.py     # Security & rate limiting
│   │   ├── logging.py      # Structured logging
│   │   └── errors.py       # Error handling
│   ├── services/           # Business logic layer
│   │   ├── network_service.py  # WiFi operations
│   │   ├── system_service.py   # System management
│   │   ├── vpn_service.py      # VPN tunnel management
│   │   └── qr_service.py       # QR code generation
│   ├── api/                # RESTful API endpoints
│   │   └── routes.py       # API v1 routes
│   ├── web/                # Web interface
│   │   └── routes.py       # Dashboard routes
│   └── system/             # Legacy compatibility
│       └── routes.py       # Backward compatibility
├── templates/              # HTML templates
├── static/                 # Static files
├── logs/                   # Application logs
├── setup-secure.sh         # Production setup script
├── requirements.txt        # Python dependencies
├── SECURITY.md            # Security documentation
└── DEPLOYMENT.md          # Deployment guide
```

### Key Improvements in v2.0

- **🏛️ Modular Architecture**: Separation of concerns with clear layers
- **🔒 Security First**: Rate limiting, input validation, CSRF protection
- **📡 RESTful API**: Versioned API with comprehensive documentation
- **🛡️ Error Handling**: Comprehensive error handling and structured logging
- **🧪 Testability**: Modular design enables easy unit testing
- **📈 Scalability**: Blueprint-based architecture for easy extension

## Quick Start

### Prerequisites

- Raspberry Pi with Raspberry Pi OS
- Two WiFi interfaces (built-in + USB WiFi adapter) or Ethernet + WiFi
- SSH access to your Raspberry Pi

### Installation

1. **Clone the repository on your development machine:**
   ```bash
   git clone <repository-url>
   cd travelnet-portal
   ```

2. **Deploy to Raspberry Pi:**
   ```bash
   # Copy files to Pi
   scp -r . pi@YOUR_PI_IP:/home/pi/travelnet-portal/
   
   # SSH into Pi
   ssh pi@YOUR_PI_IP
   
   # Navigate to project directory
   cd /home/pi/travelnet-portal
   
   # Make setup script executable and run it
   chmod +x setup.sh
   sudo ./setup.sh
   ```

3. **Access the portal:**
   - Connect to the `TravelNet-<hostname>` WiFi network (password: `TravelNet123`)
   - Open browser and go to `http://192.168.4.1`

## Configuration

### Customizing the Portal Name

Edit `config.py` and change the `APP_NAME` variable:

```python
APP_NAME = "Your Custom Portal Name"
```

### Network Interface Configuration

Update the interface names in `config.py` if needed:

```python
WIFI_INTERFACE = 'wlan1'    # External WiFi interface
AP_INTERFACE = 'wlan0'      # Access Point interface
ETHERNET_INTERFACE = 'eth0' # Ethernet interface
```

### Security Settings

For production use, update the secret key in `config.py`:

```python
SECRET_KEY = 'your-secure-secret-key-here'
```

## Manual Setup (Alternative to setup.sh)

If you prefer manual setup or need to customize the installation:

### 1. System Packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y hostapd dnsmasq iptables-persistent python3 python3-pip python3-venv git nginx ufw network-manager
```

### 2. Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Access Point Configuration

Create `/etc/hostapd/hostapd.conf`:

```
interface=wlan0
driver=nl80211
ssid=TravelNet-YourPi
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=TravelNet123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
country_code=US
ieee80211n=1
ieee80211d=1
```

### 4. DHCP Configuration

Configure `/etc/dnsmasq.conf`:

```
interface=wlan0
bind-interfaces
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,12h
dhcp-option=3,192.168.4.1
dhcp-option=6,192.168.4.1
server=8.8.8.8
server=8.8.4.4
address=/#/192.168.4.1
```

### 5. Network Configuration

Set static IP for access point interface in `/etc/systemd/network/08-wlan0.network`:

```
[Match]
Name=wlan0

[Network]
Address=192.168.4.1/24
IPMasquerade=yes
IPForward=yes
```

### 6. IP Forwarding

Enable IP forwarding:

```bash
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf
```

### 7. Firewall Rules

```bash
sudo iptables -t nat -A POSTROUTING -o wlan1 -j MASQUERADE
sudo iptables -A FORWARD -i wlan1 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i wlan0 -o wlan1 -j ACCEPT
sudo iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 80 -j DNAT --to-destination 192.168.4.1:80
# UFW is used for firewall management instead of iptables-persistent
```

### 8. Systemd Service

Create `/etc/systemd/system/travelnet.service`:

```ini
[Unit]
Description=TravelNet Portal
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/travelnet-portal
Environment=PATH=/home/pi/travelnet-portal/venv/bin
ExecStart=/home/pi/travelnet-portal/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 9. Enable Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable hostapd dnsmasq travelnet
sudo systemctl start hostapd dnsmasq travelnet
```

## Usage

### Connecting to Public WiFi

1. Connect your device to the TravelNet access point
2. Open a web browser and navigate to `http://192.168.4.1`
3. Click "Scan" to find available networks
4. Select a network and enter the password
5. Click "Connect" to establish the connection

### Generating QR Codes

1. Navigate to the "QR Connect" page
2. Enter the WiFi network details
3. Click "Generate QR Code"
4. Share the QR code with others for easy connection

### VPN Tunnel Management

1. **Setup VPN on Pi**: Deploy VPN functionality to your Raspberry Pi
   ```bash
   # Copy VPN setup script to Pi
   scp setup-vpn.sh pi@YOUR_PI_IP:~/
   
   # SSH to Pi and run setup
   ssh pi@YOUR_PI_IP
   chmod +x setup-vpn.sh && ./setup-vpn.sh
   ```

2. **Upload Configuration**: 
   - Navigate to "VPN Tunnel" page
   - Click "Upload Config"
   - Paste your WireGuard configuration
   - Save with a descriptive name

3. **Connect to VPN**:
   - Use the VPN toggle on the dashboard for quick connect/disconnect
   - Or go to VPN management page for detailed control
   - Monitor connection status and traffic

4. **Benefits**:
   - Browse as if you're at home
   - Secure tunnel through public WiFi
   - Access home network resources
   - Bypass geographic restrictions

### System Management

- **SSH Control**: Enable/disable SSH access through WiFi
- **System Reboot**: Restart the Raspberry Pi remotely
- **Status Monitoring**: View real-time connection status

## API Endpoints

### Web Interface
- `GET /` - Main dashboard
- `GET /qr-connect` - QR code generation page
- `GET /vpn-tunnel` - VPN tunnel management page

### Network API (v1)
- `GET /api/v1/networks/scan` - Scan for available networks
- `POST /api/v1/networks/connect` - Connect to WiFi network
- `POST /api/v1/networks/disconnect` - Disconnect from WiFi
- `GET /api/v1/networks/status` - Get connection status

### VPN API (v1)
- `GET /api/v1/vpn/status` - Get VPN connection status
- `POST /api/v1/vpn/connect` - Connect to VPN
- `POST /api/v1/vpn/disconnect` - Disconnect from VPN
- `GET /api/v1/vpn/configs` - List VPN configurations
- `POST /api/v1/vpn/configs` - Upload VPN configuration
- `DELETE /api/v1/vpn/configs/<name>` - Delete VPN configuration

### System API (v1)
- `GET /api/v1/system/status` - Get system status
- `POST /api/v1/system/reboot` - Reboot system
- `POST /api/v1/system/ssh/<action>` - Manage SSH (enable/disable)

### QR Code API (v1)
- `POST /api/v1/qr/generate` - Generate WiFi QR code
- `POST /api/v1/qr/parse` - Parse WiFi QR code

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py
```

### Testing on Pi

```bash
# Check service status
sudo systemctl status travelnet

# View logs
sudo journalctl -u travelnet -f

# Restart service
sudo systemctl restart travelnet
```

## Troubleshooting

### Common Issues

1. **Can't connect to access point**
   - Check if hostapd is running: `sudo systemctl status hostapd`
   - Verify interface configuration: `ip addr show wlan0`

2. **No internet after connecting to public WiFi**
   - Check if wlan1 is connected: `nmcli device status`
   - Verify IP forwarding: `cat /proc/sys/net/ipv4/ip_forward`

3. **Web interface not accessible**
   - Check if service is running: `sudo systemctl status travelnet`
   - Verify firewall rules: `sudo iptables -L -n`

### Log Files

- Application logs: `/opt/travelnet/logs/travelnet.log`
- System logs: `sudo journalctl -u travelnet`
- Network logs: `sudo journalctl -u NetworkManager`

## Security Considerations

- Change default access point password
- Update SECRET_KEY for production
- Regularly update system packages
- Monitor access logs
- Use strong passwords for SSH access

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the troubleshooting section
- Review system logs
- Open an issue on GitHub

---

**Note**: This application is designed for Raspberry Pi but can be adapted for other Linux systems with appropriate modifications to the network configuration.