"""
Configuration settings for the Travel Router Portal
"""
import os
from pathlib import Path

# Application Configuration
APP_NAME = "TravelNet Portal"  # Change this to customize your portal name
APP_VERSION = "1.0.0"
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Network Configuration
WIFI_INTERFACE = os.environ.get('WIFI_INTERFACE', 'wlan1')  # External WiFi interface
AP_INTERFACE = os.environ.get('AP_INTERFACE', 'wlan0')     # Access Point interface
ETHERNET_INTERFACE = os.environ.get('ETH_INTERFACE', 'eth0')

# File Paths
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / 'static'
TEMPLATES_DIR = BASE_DIR / 'templates'
LOGS_DIR = BASE_DIR / 'logs'

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# Logging Configuration
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FILE = LOGS_DIR / 'travelnet.log'

# Security
ALLOWED_HOSTS = ['192.168.4.1', 'localhost', '127.0.0.1']  # Add your Pi's AP IP

# VPN Configuration
SUPPORTED_VPN_TYPES = ['openvpn', 'wireguard']
VPN_CONFIG_DIR = BASE_DIR / 'vpn_configs'
VPN_CONFIG_DIR.mkdir(exist_ok=True)

# System Commands (for security, we'll validate these)
ALLOWED_SYSTEM_COMMANDS = {
    'reboot': ['sudo', 'reboot'],
    'wifi_scan': ['nmcli', '--colors', 'no', '-m', 'multiline', '--get-value', 'SSID,SECURITY', 'dev', 'wifi', 'list'],
    'wifi_connect': ['nmcli', '--colors', 'no', 'device', 'wifi', 'connect'],
    'wifi_status': ['nmcli', '--colors', 'no', 'device', 'status'],
    'enable_ssh': ['sudo', 'systemctl', 'enable', 'ssh'],
    'start_ssh': ['sudo', 'systemctl', 'start', 'ssh'],
    'stop_ssh': ['sudo', 'systemctl', 'stop', 'ssh'],
    'ssh_status': ['sudo', 'systemctl', 'is-active', 'ssh']
}