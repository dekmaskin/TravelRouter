"""
API Routes Module

RESTful API endpoints for network and system operations.
All endpoints return JSON responses and include proper error handling.
"""

import logging
from flask import Blueprint, request, jsonify, current_app

from app.core.security import security_manager
from app.core.errors import ValidationError, NetworkError, SecurityError
from app.services.network_service import NetworkService
from app.services.system_service import SystemService
from app.services.qr_service import QRCodeService

logger = logging.getLogger(__name__)

# Create API blueprint
api_bp = Blueprint('api', __name__)

# Service getters to avoid application context issues
def get_network_service():
    """Get network service instance"""
    if not hasattr(current_app, 'network_service'):
        current_app.network_service = NetworkService()
    return current_app.network_service

def get_system_service():
    """Get system service instance"""
    if not hasattr(current_app, 'system_service'):
        current_app.system_service = SystemService()
    return current_app.system_service

def get_qr_service():
    """Get QR service instance"""
    if not hasattr(current_app, 'qr_service'):
        current_app.qr_service = QRCodeService()
    return current_app.qr_service


@api_bp.route('/networks/scan', methods=['GET'])
@security_manager.rate_limit(max_requests=100)
def scan_networks():
    """
    Scan for available WiFi networks
    
    Returns:
        JSON response with list of available networks
    """
    try:
        logger.info(f"Network scan requested from {request.remote_addr}")
        
        networks = get_network_service().scan_wifi_networks()
        network_data = [network.to_dict() for network in networks]
        
        logger.info(f"Found {len(networks)} networks")
        
        return jsonify({
            'success': True,
            'networks': network_data,
            'count': len(networks)
        })
        
    except NetworkError as e:
        return jsonify({
            'success': False,
            'error': 'network_error',
            'message': str(e)
        }), 500


@api_bp.route('/networks/connect', methods=['POST'])
@security_manager.rate_limit(max_requests=50)  # Will be overridden by config at runtime
@security_manager.validate_input('json')
def connect_network():
    """
    Connect to a WiFi network
    
    Request Body:
        {
            "ssid": "network_name",
            "password": "network_password"  // optional for open networks
        }
    
    Returns:
        JSON response with connection result
    """
    try:
        data = request.get_json()
        ssid = data.get('ssid')
        password = data.get('password', '')
        
        if not ssid:
            raise ValidationError('SSID is required', 'ssid')
        
        logger.info(f"WiFi connection attempt from {request.remote_addr} to SSID: {ssid[:10]}...")
        
        result = get_network_service().connect_to_wifi(ssid, password if password else None)
        
        # Log result (without sensitive info)
        if result.success:
            logger.info(f"Successful WiFi connection to {ssid[:10]}...")
        else:
            logger.warning(f"Failed WiFi connection attempt to {ssid[:10]}...")
        
        return jsonify(result.to_dict())
        
    except (ValidationError, NetworkError) as e:
        return jsonify({
            'success': False,
            'error': type(e).__name__.lower(),
            'message': str(e)
        }), 400 if isinstance(e, ValidationError) else 500


@api_bp.route('/networks/disconnect', methods=['POST'])
@security_manager.rate_limit(max_requests=50)
def disconnect_network():
    """
    Disconnect from current WiFi network
    
    Returns:
        JSON response with disconnection result
    """
    try:
        logger.info(f"WiFi disconnection requested from {request.remote_addr}")
        
        result = get_network_service().disconnect_from_wifi()
        
        # Log result
        if result.success:
            logger.info("Successfully disconnected from WiFi")
        else:
            logger.warning("Failed WiFi disconnection attempt")
        
        return jsonify(result.to_dict())
        
    except Exception as e:
        logger.error(f"Error disconnecting from WiFi: {e}")
        return jsonify({
            'success': False,
            'error': 'disconnect_error',
            'message': 'Failed to disconnect from network'
        }), 500


@api_bp.route('/networks/status', methods=['GET'])
@security_manager.rate_limit(max_requests=200)
def get_connection_status():
    """
    Get current network connection status
    
    Returns:
        JSON response with connection status information
    """
    try:
        status = get_network_service().get_connection_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting connection status: {e}")
        return jsonify({
            'success': False,
            'error': 'status_error',
            'message': 'Failed to retrieve connection status'
        }), 500


@api_bp.route('/system/status', methods=['GET'])
@security_manager.rate_limit(max_requests=20)
def get_system_status():
    """
    Get system status information
    
    Returns:
        JSON response with system status
    """
    try:
        status = get_system_service().get_system_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({
            'success': False,
            'error': 'system_error',
            'message': 'Failed to retrieve system status'
        }), 500


@api_bp.route('/system/reboot', methods=['POST'])
@security_manager.rate_limit(max_requests=2)
def reboot_system():
    """
    Reboot the system
    
    Returns:
        JSON response with reboot result
    """
    try:
        logger.warning(f"System reboot requested from {request.remote_addr}")
        
        result = get_system_service().reboot_system()
        return jsonify(result.to_dict())
        
    except SecurityError as e:
        return jsonify({
            'success': False,
            'error': 'security_error',
            'message': 'Reboot not permitted'
        }), 403
    except Exception as e:
        logger.error(f"Error rebooting system: {e}")
        return jsonify({
            'success': False,
            'error': 'system_error',
            'message': 'Reboot operation failed'
        }), 500


@api_bp.route('/system/ssh/<action>', methods=['POST'])
@security_manager.rate_limit(max_requests=5)
def manage_ssh(action):
    """
    Manage SSH service
    
    Args:
        action: 'enable' or 'disable'
    
    Returns:
        JSON response with SSH management result
    """
    try:
        if action not in ['enable', 'disable']:
            raise ValidationError('Invalid SSH action')
        
        logger.warning(f"SSH {action} requested from {request.remote_addr}")
        
        result = get_system_service().manage_ssh(action)
        return jsonify(result.to_dict())
        
    except SecurityError as e:
        return jsonify({
            'success': False,
            'error': 'security_error',
            'message': 'SSH management not permitted'
        }), 403
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error managing SSH: {e}")
        return jsonify({
            'success': False,
            'error': 'system_error',
            'message': f'SSH {action} operation failed'
        }), 500


@api_bp.route('/qr/generate', methods=['POST'])
@security_manager.rate_limit(max_requests=20)
@security_manager.validate_input('json')
def generate_qr_code():
    """
    Generate QR code for WiFi connection
    
    Request Body:
        {
            "ssid": "network_name",
            "password": "network_password",  // optional for open networks
            "security": "WPA"  // optional, defaults to WPA
        }
    
    Returns:
        JSON response with QR code data
    """
    try:
        data = request.get_json()
        ssid = data.get('ssid')
        password = data.get('password', '')
        security = data.get('security', 'WPA')
        
        if not ssid:
            raise ValidationError('SSID is required', 'ssid')
        
        logger.info(f"QR code generation requested from {request.remote_addr} for SSID: {ssid[:10]}...")
        
        result = get_qr_service().generate_wifi_qr(ssid, password, security)
        return jsonify(result.to_dict())
        
    except (ValidationError, SecurityError) as e:
        return jsonify({
            'success': False,
            'error': type(e).__name__.lower(),
            'message': str(e)
        }), 400 if isinstance(e, ValidationError) else 403
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        return jsonify({
            'success': False,
            'error': 'qr_error',
            'message': 'QR code generation failed'
        }), 500


@api_bp.route('/qr/parse', methods=['POST'])
@security_manager.rate_limit(max_requests=30)
@security_manager.validate_input('json')
def parse_qr_code():
    """
    Parse WiFi QR code data
    
    Request Body:
        {
            "qr_data": "WIFI:T:WPA;S:MyNetwork;P:MyPassword;;"
        }
    
    Returns:
        JSON response with parsed WiFi network information
    """
    try:
        data = request.get_json()
        qr_data = data.get('qr_data')
        
        if not qr_data:
            raise ValidationError('QR data is required', 'qr_data')
        
        logger.info(f"QR code parsing requested from {request.remote_addr}")
        
        parsed_data = get_qr_service().parse_wifi_qr(qr_data)
        
        if parsed_data:
            return jsonify({
                'success': True,
                'network': parsed_data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'invalid_qr',
                'message': 'QR code does not contain valid WiFi network information'
            }), 400
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error parsing QR code: {e}")
        return jsonify({
            'success': False,
            'error': 'parse_error',
            'message': 'Failed to parse QR code'
        }), 500


# API documentation endpoint
@api_bp.route('/docs', methods=['GET'])
def api_documentation():
    """
    API documentation endpoint
    
    Returns:
        JSON response with API documentation
    """
    docs = {
        'version': '1.0',
        'title': 'TravelNet Portal API',
        'description': 'RESTful API for travel router management',
        'endpoints': {
            'GET /api/v1/networks/scan': 'Scan for available WiFi networks',
            'POST /api/v1/networks/connect': 'Connect to a WiFi network',
            'GET /api/v1/networks/status': 'Get current connection status',
            'GET /api/v1/system/status': 'Get system status',
            'POST /api/v1/system/reboot': 'Reboot the system',
            'POST /api/v1/system/ssh/<action>': 'Manage SSH service (enable/disable)',
            'POST /api/v1/qr/generate': 'Generate WiFi QR codes',
            'POST /api/v1/qr/parse': 'Parse WiFi QR code data',
            'GET /api/v1/docs': 'This documentation'
        },
        'rate_limits': {
            'network_scan': '10 requests per minute',
            'network_connect': '5 requests per minute',
            'status_checks': '20-30 requests per minute',
            'system_operations': '2-5 requests per minute'
        },
        'authentication': 'None (local network access only)',
        'response_format': 'JSON'
    }
    
    return jsonify(docs)