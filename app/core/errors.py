"""
Error Handling Module

Centralized error handling with proper HTTP status codes,
logging, and user-friendly error messages.
"""

import logging
from flask import jsonify, render_template, request, current_app
from werkzeug.exceptions import HTTPException, BadRequest, TooManyRequests, Forbidden, NotFound
from werkzeug.http import HTTP_STATUS_CODES

logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')


class TravelNetError(Exception):
    """Base exception class for TravelNet Portal"""
    
    def __init__(self, message: str, status_code: int = 500, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload


class NetworkError(TravelNetError):
    """Network-related errors"""
    pass


class ValidationError(TravelNetError):
    """Input validation errors"""
    
    def __init__(self, message: str, field: str = None):
        super().__init__(message, 400)
        self.field = field


class SecurityError(TravelNetError):
    """Security-related errors"""
    
    def __init__(self, message: str, status_code: int = 403):
        super().__init__(message, status_code)


def register_error_handlers(app):
    """Register error handlers with the Flask application"""
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle validation errors"""
        logger.warning(f"Validation error: {error.message}")
        
        response = {
            'success': False,
            'error': 'validation_error',
            'message': error.message
        }
        
        if error.field:
            response['field'] = error.field
            
        return jsonify(response), error.status_code
    
    @app.errorhandler(NetworkError)
    def handle_network_error(error):
        """Handle network-related errors"""
        logger.error(f"Network error: {error.message}")
        
        return jsonify({
            'success': False,
            'error': 'network_error',
            'message': error.message
        }), error.status_code
    
    @app.errorhandler(SecurityError)
    def handle_security_error(error):
        """Handle security-related errors"""
        security_logger.warning(f"Security error: {error.message}")
        
        return jsonify({
            'success': False,
            'error': 'security_error',
            'message': 'Access denied'
        }), error.status_code
    
    @app.errorhandler(BadRequest)
    def handle_bad_request(error):
        """Handle 400 Bad Request errors"""
        logger.warning(f"Bad request: {error.description}")
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'bad_request',
                'message': error.description or 'Invalid request'
            }), 400
        
        return render_template('error.html', 
                             error='Bad Request',
                             message=error.description), 400
    
    @app.errorhandler(Forbidden)
    def handle_forbidden(error):
        """Handle 403 Forbidden errors"""
        security_logger.warning(f"Forbidden access attempt from {request.remote_addr}")
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'forbidden',
                'message': 'Access denied'
            }), 403
        
        return render_template('error.html',
                             error='Access Denied',
                             message='You do not have permission to access this resource'), 403
    
    @app.errorhandler(NotFound)
    def handle_not_found(error):
        """Handle 404 Not Found errors"""
        logger.info(f"404 error for {request.url}")
        
        # Check if this is a captive portal detection request
        user_agent = request.headers.get('User-Agent', '').lower()
        host = request.headers.get('Host', '')
        
        # Captive portal detection patterns
        captive_patterns = [
            'captivenetworksupport', 'wispr', 'connectivitycheck',
            'networkcheck', 'internet-check'
        ]
        
        if any(pattern in user_agent for pattern in captive_patterns) or host not in current_app.config['ALLOWED_HOSTS']:
            return render_template('captive_portal.html', 
                                 app_name=current_app.config['APP_NAME'])
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'not_found',
                'message': 'Resource not found'
            }), 404
        
        return render_template('error.html',
                             error='Page Not Found',
                             message='The requested page could not be found'), 404
    
    @app.errorhandler(TooManyRequests)
    def handle_rate_limit(error):
        """Handle 429 Too Many Requests errors"""
        security_logger.warning(f"Rate limit exceeded from {request.remote_addr}")
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'rate_limit_exceeded',
                'message': 'Too many requests. Please try again later.'
            }), 429
        
        return render_template('error.html',
                             error='Rate Limit Exceeded',
                             message='Too many requests. Please wait before trying again.'), 429
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 Internal Server Error"""
        logger.error(f"Internal server error: {error}", exc_info=True)
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'internal_error',
                'message': 'An internal error occurred'
            }), 500
        
        return render_template('error.html',
                             error='Internal Server Error',
                             message='An unexpected error occurred. Please try again later.'), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle all other HTTP exceptions"""
        logger.warning(f"HTTP {error.code} error: {error.description}")
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': f'http_{error.code}',
                'message': error.description or HTTP_STATUS_CODES.get(error.code, 'Unknown error')
            }), error.code
        
        return render_template('error.html',
                             error=f'Error {error.code}',
                             message=error.description), error.code
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors"""
        logger.error(f"Unexpected error: {error}", exc_info=True)
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'unexpected_error',
                'message': 'An unexpected error occurred'
            }), 500
        
        return render_template('error.html',
                             error='Unexpected Error',
                             message='An unexpected error occurred. Please try again later.'), 500