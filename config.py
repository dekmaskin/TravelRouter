"""
Legacy Configuration Module

This module provides backward compatibility for the old monolithic app.py.
For new development, use app.core.config instead.
"""

import warnings
from app.core.config import Config

# Issue deprecation warning
warnings.warn(
    "config.py is deprecated. Use app.core.config.Config instead.",
    DeprecationWarning,
    stacklevel=2
)

# Export configuration for backward compatibility
_config = Config()

# Application Configuration
APP_NAME = _config.APP_NAME
APP_VERSION = _config.APP_VERSION
SECRET_KEY = _config.SECRET_KEY

# Network Configuration
WIFI_INTERFACE = _config.WIFI_INTERFACE
AP_INTERFACE = _config.AP_INTERFACE
ETHERNET_INTERFACE = _config.ETHERNET_INTERFACE

# File Paths
BASE_DIR = _config.BASE_DIR
STATIC_DIR = _config.STATIC_DIR
TEMPLATES_DIR = _config.TEMPLATES_DIR
LOGS_DIR = _config.LOGS_DIR

# Logging Configuration
LOG_LEVEL = _config.LOG_LEVEL
LOG_FILE = _config.LOG_FILE

# Security Configuration
ALLOWED_HOSTS = _config.ALLOWED_HOSTS
MAX_REQUESTS_PER_MINUTE = _config.MAX_REQUESTS_PER_MINUTE
MAX_CONNECTION_ATTEMPTS = _config.MAX_CONNECTION_ATTEMPTS

# System Commands
ALLOWED_SYSTEM_COMMANDS = _config.ALLOWED_SYSTEM_COMMANDS

# Input validation
SSID_PATTERN = _config.SSID_PATTERN
PASSWORD_MIN_LENGTH = _config.PASSWORD_MIN_LENGTH
PASSWORD_MAX_LENGTH = _config.PASSWORD_MAX_LENGTH

# Default network settings
DEFAULT_AP_SSID = _config.DEFAULT_AP_SSID
DEFAULT_AP_PASSWORD = _config.DEFAULT_AP_PASSWORD

# Feature flags
ENABLE_SYSTEM_REBOOT = _config.ENABLE_SYSTEM_REBOOT
ENABLE_QR_GENERATION = _config.ENABLE_QR_GENERATION