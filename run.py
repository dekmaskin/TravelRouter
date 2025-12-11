#!/usr/bin/env python3
"""
TravelNet Portal Application Entry Point

Production-ready Flask application with proper configuration management,
logging, and error handling.
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.core.config import config

def main():
    """Main application entry point"""
    # Determine configuration based on environment
    config_name = os.environ.get('FLASK_ENV', 'production')
    
    # Create application instance
    app = create_app(config[config_name])
    
    # Get configuration
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', '80'))
    debug = config_name == 'development'
    
    # Log startup information
    app.logger.info(f"Starting {app.config['APP_NAME']} v{app.config['APP_VERSION']}")
    app.logger.info(f"Configuration: {config_name}")
    app.logger.info(f"Debug mode: {debug}")
    app.logger.info(f"Listening on: {host}:{port}")
    
    # Start the application
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        app.logger.info("Application stopped by user")
    except Exception as e:
        app.logger.error(f"Application failed to start: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()