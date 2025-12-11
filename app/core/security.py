"""
Security Management Module

Comprehensive security features including rate limiting, input validation,
CSRF protection, and security headers.
"""

import time
import re
from collections import defaultdict
from functools import wraps
from typing import Dict, List, Optional

from flask import request, current_app, jsonify
from werkzeug.exceptions import BadRequest, TooManyRequests
import logging

logger = logging.getLogger(__name__)


class SecurityManager:
    """Centralized security management"""
    
    def __init__(self):
        self.request_counts: Dict[str, List[float]] = defaultdict(list)
        self.blocked_ips: Dict[str, float] = {}
        
    def init_app(self, app):
        """Initialize security manager with Flask app"""
        self.app = app
        
        # Add security headers to all responses
        @app.after_request
        def add_security_headers(response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; font-src 'self' https://cdnjs.cloudflare.com; img-src 'self' data:;"
            return response
    
    def rate_limit(self, max_requests: Optional[int] = None, window: int = 60):
        """Rate limiting decorator"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                client_ip = self._get_client_ip()
                
                # Check if IP is blocked
                if self._is_ip_blocked(client_ip):
                    logger.warning(f"Blocked IP {client_ip} attempted access")
                    raise TooManyRequests("IP temporarily blocked due to excessive requests")
                
                limit = max_requests or current_app.config['MAX_REQUESTS_PER_MINUTE']
                
                if not self._check_rate_limit(client_ip, limit, window):
                    logger.warning(f"Rate limit exceeded for {client_ip}")
                    self._block_ip(client_ip)
                    raise TooManyRequests("Rate limit exceeded. Please try again later.")
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def validate_input(self, data_type: str = 'json'):
        """Input validation decorator"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if data_type == 'json':
                    if not request.is_json:
                        raise BadRequest("Content-Type must be application/json")
                    
                    data = request.get_json()
                    if not data:
                        raise BadRequest("Invalid JSON data")
                    
                    # Validate SSID (only for network requests)
                    if 'ssid' in data:
                        if not self._validate_ssid(data['ssid']):
                            raise BadRequest("Invalid SSID format")
                    
                    # Validate password (only for network requests)
                    if 'password' in data and data['password']:
                        if not self._validate_password(data['password']):
                            raise BadRequest("Invalid password format or length")
                    
                    # Validate config_name (for VPN requests)
                    if 'config_name' in data:
                        config_name = data['config_name']
                        logger.info(f"Validating config name: {config_name}")
                        if not self._validate_config_name(config_name):
                            logger.error(f"Config name validation failed for: {config_name}")
                            raise BadRequest("Invalid configuration name format")
                        logger.info(f"Config name validation passed for: {config_name}")
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def _get_client_ip(self) -> str:
        """Get client IP address with proxy support"""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        return request.remote_addr or 'unknown'
    
    def _check_rate_limit(self, client_ip: str, limit: int, window: int) -> bool:
        """Check if client is within rate limits"""
        now = time.time()
        window_start = now - window
        
        # Clean old requests
        self.request_counts[client_ip] = [
            req_time for req_time in self.request_counts[client_ip]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.request_counts[client_ip]) >= limit:
            return False
        
        # Add current request
        self.request_counts[client_ip].append(now)
        return True
    
    def _is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP is currently blocked"""
        if client_ip in self.blocked_ips:
            # Check if block has expired (2 minute block)
            if time.time() - self.blocked_ips[client_ip] > 120:
                del self.blocked_ips[client_ip]
                return False
            return True
        return False
    
    def _block_ip(self, client_ip: str, duration: int = 120):
        """Block IP for specified duration (default 2 minutes)"""
        self.blocked_ips[client_ip] = time.time()
        logger.warning(f"IP {client_ip} blocked for {duration} seconds")
    
    def _validate_ssid(self, ssid: str) -> bool:
        """Validate SSID format"""
        if not ssid or not isinstance(ssid, str):
            return False
        return bool(re.match(current_app.config['SSID_PATTERN'], ssid))
    
    def _validate_password(self, password: str) -> bool:
        """Validate password format and length"""
        if not isinstance(password, str):
            return False
        
        min_len = current_app.config['PASSWORD_MIN_LENGTH']
        max_len = current_app.config['PASSWORD_MAX_LENGTH']
        
        return min_len <= len(password) <= max_len
    
    def _validate_config_name(self, config_name: str) -> bool:
        """Validate VPN configuration name format"""
        if not config_name or not isinstance(config_name, str):
            return False
        
        # Allow alphanumeric, hyphens, underscores, max 50 chars
        pattern = r'^[a-zA-Z0-9\-_]+$'
        return bool(re.match(pattern, config_name)) and len(config_name) <= 50
    
    @staticmethod
    def sanitize_ssid(ssid: str) -> Optional[str]:
        """Sanitize SSID for safe use"""
        if not ssid or not isinstance(ssid, str):
            return None
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[^\w\s\-\.]', '', ssid)
        return sanitized[:32] if sanitized else None


# Global security manager instance
security_manager = SecurityManager()