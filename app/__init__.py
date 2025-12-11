"""
TravelNet Portal Application Factory

A professional Flask application factory pattern implementation
for the TravelNet Portal travel router management system.
"""

from flask import Flask
from flask.logging import default_handler
import logging
import os
from datetime import timedelta

from app.core.config import Config
from app.core.security import SecurityManager
from app.core.logging import setup_logging


def create_app(config_class=Config):
    """
    Application factory pattern implementation.
    
    Args:
        config_class: Configuration class to use
        
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    app.config.from_object(config_class)
    
    # Configure session
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    
    # Initialize logging
    setup_logging(app)
    
    # Initialize security manager
    security_manager = SecurityManager()
    security_manager.init_app(app)
    
    # Register blueprints
    from app.api.routes import api_bp
    from app.web.routes import web_bp
    from app.system.routes import system_bp
    
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(system_bp, url_prefix='/system')
    
    # Register error handlers
    from app.core.errors import register_error_handlers
    register_error_handlers(app)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Application health check endpoint"""
        return {'status': 'healthy', 'version': app.config['APP_VERSION']}, 200
    
    return app