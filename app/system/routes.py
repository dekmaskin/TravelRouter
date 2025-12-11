"""
System Management Routes Module

Legacy compatibility routes for system operations.
These routes maintain backward compatibility with existing frontend code.
"""

import logging
from flask import Blueprint, request, jsonify

from app.core.security import security_manager
from app.services.system_service import SystemService
from app.services.network_service import NetworkService
from app.services.qr_service import QRCodeService

logger = logging.getLogger(__name__)

# Create system blueprint
system_bp = Blueprint('system', __name__)

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


@system_bp.route('/connect', methods=['POST'])
@security_manager.rate_limit(max_requests=5)
@security_manager.validate_input('json')
def connect_wifi():
    """
    Legacy route for WiFi connection
    Redirects to API endpoint for consistency
    """
    try:
        data = request.get_json()
        ssid = data.get('ssid')
        password = data.get('password', '')
        
        result = get_network_service().connect_to_wifi(ssid, password if password else None)
        return jsonify(result.to_dict())
        
    except Exception as e:
        logger.error(f"Error in legacy connect route: {e}")
        return jsonify({
            'success': False,
            'message': 'Connection failed'
        }), 500


@system_bp.route('/scan', methods=['GET'])
@security_manager.rate_limit(max_requests=10)
def scan_networks():
    """
    Legacy route for network scanning
    Redirects to API endpoint for consistency
    """
    try:
        networks = get_network_service().scan_wifi_networks()
        return jsonify({
            'success': True,
            'networks': [network.to_dict() for network in networks]
        })
        
    except Exception as e:
        logger.error(f"Error in legacy scan route: {e}")
        return jsonify({
            'success': False,
            'message': 'Network scan failed'
        }), 500


@system_bp.route('/status', methods=['GET'])
@security_manager.rate_limit(max_requests=30)
def get_status():
    """
    Legacy route for system status
    Combines network and system status for backward compatibility
    """
    try:
        network_status = get_network_service().get_connection_status()
        system_status = get_system_service().get_system_status()
        
        # Combine statuses for legacy compatibility
        combined_status = {
            'success': True,
            'connection_status': network_status.get('device_status', {}),
            'connected': network_status.get('connected', False),
            'current_network': network_status.get('current_network'),
            'ssh_active': False,  # Default value
            'timestamp': system_status.get('timestamp')
        }
        
        # Add SSH status if available
        if 'services' in system_status and 'ssh' in system_status['services']:
            combined_status['ssh_active'] = system_status['services']['ssh'].get('enabled', False)
        
        return jsonify(combined_status)
        
    except Exception as e:
        logger.error(f"Error in legacy status route: {e}")
        return jsonify({
            'success': False,
            'message': 'Status check failed'
        }), 500


@system_bp.route('/connection-status', methods=['GET'])
@security_manager.rate_limit(max_requests=30)
def get_connection_status():
    """
    Legacy route for connection status
    Maintains exact compatibility with existing frontend
    """
    try:
        status = get_network_service().get_connection_status()
        
        # Format for legacy compatibility
        legacy_status = {
            'success': status.get('success', False),
            'connected': status.get('connected', False),
            'current_network': status.get('current_network'),
            'device_connected': status.get('connected', False),
            'active_connection': None,
            'timestamp': status.get('timestamp', '')
        }
        
        # Extract active connection name for legacy compatibility
        if status.get('current_network'):
            legacy_status['active_connection'] = status['current_network']['ssid']
        
        return jsonify(legacy_status)
        
    except Exception as e:
        logger.error(f"Error in legacy connection status route: {e}")
        return jsonify({
            'success': False,
            'message': 'Connection status check failed'
        }), 500


@system_bp.route('/<action>', methods=['POST'])
@security_manager.rate_limit(max_requests=5)
def system_action(action):
    """
    Legacy route for system actions
    Maintains compatibility with existing frontend code
    """
    try:
        if action == 'reboot':
            result = get_system_service().reboot_system()
            return jsonify(result.to_dict())
        elif action in ['ssh_enable', 'ssh_disable']:
            ssh_action = 'enable' if action == 'ssh_enable' else 'disable'
            result = get_system_service().manage_ssh(ssh_action)
            return jsonify(result.to_dict())
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid system action'
            }), 400
        
    except Exception as e:
        logger.error(f"Error in legacy system action {action}: {e}")
        return jsonify({
            'success': False,
            'message': f'System action {action} failed'
        }), 500


@system_bp.route('/generate-qr', methods=['POST'])
@security_manager.rate_limit(max_requests=20)
@security_manager.validate_input('json')
def generate_qr():
    """
    Legacy route for QR code generation
    Maintains compatibility with existing frontend code
    """
    try:
        data = request.get_json()
        ssid = data.get('ssid')
        password = data.get('password', '')
        security = data.get('security', 'WPA')
        
        result = get_qr_service().generate_wifi_qr(ssid, password, security)
        return jsonify(result.to_dict())
        
    except Exception as e:
        logger.error(f"Error in legacy QR generation route: {e}")
        return jsonify({
            'success': False,
            'message': 'QR code generation failed'
        }), 500


@system_bp.route('/parse-qr', methods=['POST'])
@security_manager.rate_limit(max_requests=30)
@security_manager.validate_input('json')
def parse_qr():
    """
    Legacy route for QR code parsing
    Maintains compatibility with existing frontend code
    """
    try:
        data = request.get_json()
        qr_data = data.get('qr_data')
        
        parsed_data = get_qr_service().parse_wifi_qr(qr_data)
        
        if parsed_data:
            return jsonify({
                'success': True,
                'network': parsed_data
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid QR code format'
            }), 400
        
    except Exception as e:
        logger.error(f"Error in legacy QR parsing route: {e}")
        return jsonify({
            'success': False,
            'message': 'QR code parsing failed'
        }), 500