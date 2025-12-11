"""
Logging Configuration Module

Professional logging setup with structured logging, log rotation,
and security-aware log filtering.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from flask import Flask, request, has_request_context
import json
from datetime import datetime


class SecurityFilter(logging.Filter):
    """Filter to remove sensitive information from logs"""
    
    SENSITIVE_KEYS = ['password', 'secret', 'key', 'token', 'auth']
    
    def filter(self, record):
        """Filter sensitive information from log records"""
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            # Basic password filtering
            for key in self.SENSITIVE_KEYS:
                if key in record.msg.lower():
                    record.msg = record.msg.replace(
                        record.msg[record.msg.lower().find(key):record.msg.lower().find(key) + 50],
                        f"{key}=[REDACTED]"
                    )
        return True


class RequestFormatter(logging.Formatter):
    """Custom formatter that includes request context"""
    
    def format(self, record):
        """Format log record with request context if available"""
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
            record.method = request.method
        else:
            record.url = None
            record.remote_addr = None
            record.method = None
        
        return super().format(record)


class StructuredFormatter(logging.Formatter):
    """JSON structured logging formatter"""
    
    def format(self, record):
        """Format log record as structured JSON"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add request context if available
        if has_request_context():
            log_entry.update({
                'request': {
                    'method': request.method,
                    'url': request.url,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')
                }
            })
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


def setup_logging(app: Flask):
    """
    Configure comprehensive logging for the application
    
    Args:
        app: Flask application instance
    """
    # Ensure logs directory exists
    logs_dir = Path(app.config['LOGS_DIR'])
    logs_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
    
    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with request context
    console_handler = logging.StreamHandler()
    console_formatter = RequestFormatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(SecurityFilter())
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_formatter = RequestFormatter(
        '[%(asctime)s] %(levelname)s %(name)s: %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(SecurityFilter())
    
    # Structured JSON handler for analysis
    json_handler = logging.handlers.RotatingFileHandler(
        logs_dir / 'travelnet.json.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=3
    )
    json_handler.setFormatter(StructuredFormatter())
    json_handler.addFilter(SecurityFilter())
    
    # Security events handler
    security_handler = logging.handlers.RotatingFileHandler(
        logs_dir / 'security.log',
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=10
    )
    security_formatter = RequestFormatter(
        '[%(asctime)s] SECURITY %(levelname)s: %(message)s'
    )
    security_handler.setFormatter(security_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    if app.config.get('STRUCTURED_LOGGING', True):
        root_logger.addHandler(json_handler)
    
    # Configure security logger
    security_logger = logging.getLogger('security')
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.WARNING)
    
    # Configure Flask's logger
    app.logger.handlers = []
    app.logger.propagate = True
    
    # Configure werkzeug logger (less verbose)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    app.logger.info(f"Logging configured - Level: {app.config['LOG_LEVEL']}")


def get_security_logger():
    """Get the security-specific logger"""
    return logging.getLogger('security')