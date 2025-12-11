"""
Application Configuration Management

Centralized configuration management with environment-based settings,
validation, and secure defaults.
"""

import os
import secrets
import re
from pathlib import Path
from typing import List, Dict, Any


def _get_version():
    """Get version from VERSION file"""
    try:
        version_file = Path(__file__).parent.parent.parent / 'VERSION'
        if version_file.exists():
            return version_file.read_text().strip()
    except Exception:
        pass
    return "1.0.0"  # fallback version


class Config:
    """Base configuration class with secure defaults"""
    
    # Application Settings
    APP_NAME = os.environ.get('APP_NAME', 'TravelNet Portal')
    APP_VERSION = _get_version()
    
    # Security Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Network Interface Configuration
    WIFI_INTERFACE = os.environ.get('WIFI_INTERFACE', 'wlan1')
    AP_INTERFACE = os.environ.get('AP_INTERFACE', 'wlan0')
    ETHERNET_INTERFACE = os.environ.get('ETH_INTERFACE', 'eth0')
    
    # File Paths
    BASE_DIR = Path(__file__).parent.parent.parent
    STATIC_DIR = BASE_DIR / 'static'
    TEMPLATES_DIR = BASE_DIR / 'templates'
    LOGS_DIR = BASE_DIR / 'logs'
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = LOGS_DIR / 'travelnet.log'
    
    # Security Settings
    ALLOWED_HOSTS = [
        '192.168.4.1',
        'localhost',
        '127.0.0.1',
        'router.local',
        'travel.router',
        'portal.local'
    ]
    
    # Rate Limiting - Relaxed for local travel router use
    MAX_REQUESTS_PER_MINUTE = int(os.environ.get('MAX_REQUESTS_PER_MINUTE', '300'))
    MAX_CONNECTION_ATTEMPTS = int(os.environ.get('MAX_CONNECTION_ATTEMPTS', '20'))
    
    # Input Validation
    SSID_PATTERN = r'^[a-zA-Z0-9\s\-_\.]{1,32}$'
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 63
    
    # Default Network Settings
    DEFAULT_AP_SSID = os.environ.get('DEFAULT_AP_SSID', 'TravelNet-Portal')
    DEFAULT_AP_PASSWORD = os.environ.get('DEFAULT_AP_PASSWORD', 'TravelNet2026!')
    AP_IP = os.environ.get('AP_IP', '192.168.4.1')
    
    # Feature Flags
    ENABLE_SSH_MANAGEMENT = os.environ.get('ENABLE_SSH_MANAGEMENT', 'true').lower() == 'true'
    ENABLE_SYSTEM_REBOOT = os.environ.get('ENABLE_SYSTEM_REBOOT', 'true').lower() == 'true'
    ENABLE_QR_GENERATION = os.environ.get('ENABLE_QR_GENERATION', 'true').lower() == 'true'
    ENABLE_VPN_TUNNEL = os.environ.get('ENABLE_VPN_TUNNEL', 'true').lower() == 'true'
    
    # System Commands Whitelist
    ALLOWED_SYSTEM_COMMANDS = {
        'reboot': ['sudo', 'reboot'],
        'wifi_scan': ['nmcli', '--colors', 'no', '-t', '-f', 'SSID,SECURITY,SIGNAL', 'dev', 'wifi', 'list'],
        'wifi_connect': ['nmcli', 'device', 'wifi', 'connect'],
        'wifi_status': ['nmcli', '--colors', 'no', 'device', 'status'],
        'enable_ssh': ['sudo', 'systemctl', 'enable', 'ssh'],
        'start_ssh': ['sudo', 'systemctl', 'start', 'ssh'],
        'stop_ssh': ['sudo', 'systemctl', 'stop', 'ssh'],
        'ssh_status': ['sudo', 'systemctl', 'is-active', 'ssh']
    }
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with configuration"""
        # Ensure directories exist
        cls.LOGS_DIR.mkdir(exist_ok=True)
        cls.STATIC_DIR.mkdir(exist_ok=True)
        cls.TEMPLATES_DIR.mkdir(exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration with enhanced security"""
    DEBUG = False
    TESTING = False
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Stricter rate limiting
    MAX_REQUESTS_PER_MINUTE = int(os.environ.get('MAX_REQUESTS_PER_MINUTE', '30'))
    MAX_CONNECTION_ATTEMPTS = int(os.environ.get('MAX_CONNECTION_ATTEMPTS', '3'))


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    
    # Use in-memory storage for testing
    LOG_LEVEL = 'WARNING'


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}