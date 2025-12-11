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
from app.services.vpn_service import VPNService
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

def get_vpn_service():
    """Get VPN service instance"""
    if not hasattr(current_app, 'vpn_service'):
        current_app.vpn_service = VPNService()
    return current_app.vpn_service


@api_bp.route('/networks/scan', methods=['GET'])
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_NORMAL'])
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
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_LOW'])
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
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_LOW'])
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
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_HIGH'])
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
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_HIGH'])
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
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_CRITICAL'])
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


@api_bp.route('/system/restart-network', methods=['POST'])
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_LOW'])
def restart_network():
    """
    Restart network services
    
    Returns:
        JSON response with network restart result
    """
    try:
        logger.warning(f"Network restart requested from {request.remote_addr}")
        
        result = get_system_service().restart_network()
        return jsonify(result.to_dict())
        
    except Exception as e:
        logger.error(f"Error restarting network: {e}")
        return jsonify({
            'success': False,
            'error': 'network_restart_error',
            'message': 'Network restart failed'
        }), 500


@api_bp.route('/system/update', methods=['POST'])
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_NORMAL'])
def update_system():
    """
    Update the system using the update script
    
    Returns:
        JSON response with update result
    """
    try:
        logger.warning(f"System update requested from {request.remote_addr}")
        
        result = get_system_service().update_system()
        return jsonify(result.to_dict())
        
    except SecurityError as e:
        return jsonify({
            'success': False,
            'error': 'security_error',
            'message': 'System update not permitted'
        }), 403
    except Exception as e:
        logger.error(f"Error updating system: {e}")
        return jsonify({
            'success': False,
            'error': 'system_update_error',
            'message': 'System update failed'
        }), 500


@api_bp.route('/system/update/status', methods=['GET'])
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_HIGH'])
def get_update_status():
    """
    Get current system update status
    
    Returns:
        JSON response with update status
    """
    try:
        status = get_system_service().get_update_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting update status: {e}")
        return jsonify({
            'success': False,
            'error': 'update_status_error',
            'message': 'Failed to retrieve update status'
        }), 500


@api_bp.route('/system/logs', methods=['GET'])
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_NORMAL'])
def get_system_logs():
    """
    Get system logs
    
    Query Parameters:
        type: Log type ('application', 'system', 'network')
        lines: Number of lines to retrieve (default: 100)
    
    Returns:
        JSON response with log content
    """
    try:
        log_type = request.args.get('type', 'application')
        lines = int(request.args.get('lines', 100))
        
        logger.info(f"System logs requested from {request.remote_addr}, type: {log_type}")
        
        result = get_system_service().get_system_logs(log_type, lines)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting system logs: {e}")
        return jsonify({
            'success': False,
            'error': 'logs_error',
            'message': 'Failed to retrieve system logs'
        }), 500


# Hotspot Management Endpoints

@api_bp.route('/hotspot/config', methods=['GET'])
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_NORMAL'])
def get_hotspot_config():
    """
    Get current hotspot configuration
    
    Returns:
        JSON response with hotspot configuration
    """
    try:
        logger.info(f"Hotspot config requested from {request.remote_addr}")
        
        config = get_network_service().get_hotspot_credentials()
        return jsonify({
            'success': True,
            'config': config
        })
        
    except Exception as e:
        logger.error(f"Error getting hotspot config: {e}")
        return jsonify({
            'success': False,
            'error': 'hotspot_config_error',
            'message': 'Failed to get hotspot configuration'
        }), 500


@api_bp.route('/hotspot/config', methods=['POST'])
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_LOW'])
@security_manager.validate_input('json')
def update_hotspot_config():
    """
    Update hotspot configuration
    
    Request Body:
        {
            "ssid": "MyHotspot",
            "password": "MyPassword",  // optional for open network
            "visible": true,           // optional, default true
            "enabled": true            // optional, default true
        }
    
    Returns:
        JSON response with update result
    """
    try:
        data = request.get_json()
        ssid = data.get('ssid', '').strip()
        password = data.get('password', '').strip()
        visible = data.get('visible', True)
        enabled = data.get('enabled', True)
        
        if not ssid:
            raise ValidationError('SSID is required', 'ssid')
        
        logger.info(f"Hotspot config update requested from {request.remote_addr} for SSID: {ssid[:10]}...")
        
        result = get_network_service().update_hotspot_config(ssid, password, visible, enabled)
        
        # Log result (without sensitive info)
        if result.success:
            logger.info(f"Successfully updated hotspot config for SSID: {ssid[:10]}...")
        else:
            logger.warning(f"Failed to update hotspot config for SSID: {ssid[:10]}...")
        
        return jsonify(result.to_dict())
        
    except (ValidationError, NetworkError) as e:
        return jsonify({
            'success': False,
            'error': type(e).__name__.lower(),
            'message': str(e)
        }), 400 if isinstance(e, ValidationError) else 500
    except Exception as e:
        logger.error(f"Error updating hotspot config: {e}")
        return jsonify({
            'success': False,
            'error': 'hotspot_update_error',
            'message': 'Failed to update hotspot configuration'
        }), 500


@api_bp.route('/system/interfaces', methods=['GET'])
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_NORMAL'])
def get_network_interfaces():
    """
    Get information about network interfaces
    
    Returns:
        JSON response with interface information
    """
    try:
        logger.info(f"Network interfaces info requested from {request.remote_addr}")
        
        network_service = get_network_service()
        
        # Get configured interfaces
        configured = {
            'wifi_interface': network_service.wifi_interface,
            'ap_interface': network_service.ap_interface,
            'ethernet_interface': current_app.config['ETHERNET_INTERFACE']
        }
        
        # Get available WiFi interfaces
        available_wifi = network_service._get_available_wifi_interfaces()
        
        # Check AP interface status
        ap_check = network_service._check_ap_interface()
        
        return jsonify({
            'success': True,
            'configured': configured,
            'available_wifi_interfaces': available_wifi,
            'ap_interface_status': ap_check
        })
        
    except Exception as e:
        logger.error(f"Error getting network interfaces: {e}")
        return jsonify({
            'success': False,
            'error': 'interfaces_error',
            'message': 'Failed to get network interface information'
        }), 500





@api_bp.route('/qr/hotspot', methods=['GET'])
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_NORMAL'])
def get_hotspot_qr():
    """
    Get QR code for the travel router's hotspot
    
    Returns:
        JSON response with hotspot QR code and credentials
    """
    try:
        logger.info(f"Hotspot QR code requested from {request.remote_addr}")
        
        # Get actual hotspot credentials from system
        hotspot_config = get_network_service().get_hotspot_credentials()
        ssid = hotspot_config['ssid']
        password = hotspot_config['password']
        security = hotspot_config['security']
        
        # Generate QR code for hotspot
        result = get_qr_service().generate_wifi_qr(ssid, password, security)
        
        if result.success:
            # Add password to response for display
            response_data = result.to_dict()
            response_data['password'] = password
            return jsonify(response_data)
        else:
            return jsonify(result.to_dict()), 500
        
    except Exception as e:
        logger.error(f"Error generating hotspot QR code: {e}")
        return jsonify({
            'success': False,
            'error': 'hotspot_qr_error',
            'message': 'Failed to generate hotspot QR code'
        }), 500


@api_bp.route('/qr/generate', methods=['POST'])
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_NORMAL'])
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
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_NORMAL'])
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


# VPN Management Endpoints

@api_bp.route('/vpn/status', methods=['GET'])
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_HIGH'])
def get_vpn_status():
    """
    Get current VPN connection status
    
    Returns:
        JSON response with VPN status information
    """
    try:
        status = get_vpn_service().get_vpn_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting VPN status: {e}")
        return jsonify({
            'success': False,
            'error': 'vpn_status_error',
            'message': 'Failed to retrieve VPN status'
        }), 500


@api_bp.route('/vpn/connect', methods=['POST'])
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_LOW'])
@security_manager.validate_input('json')
def connect_vpn():
    """
    Connect to VPN using specified configuration
    
    Request Body:
        {
            "config_name": "home_server"
        }
    
    Returns:
        JSON response with VPN connection result
    """
    try:
        logger.info(f"VPN connect request received from {request.remote_addr}")
        logger.info(f"Request content type: {request.content_type}")
        logger.info(f"Request data: {request.get_data()}")
        
        data = request.get_json()
        logger.info(f"Parsed JSON data: {data}")
        
        config_name = data.get('config_name')
        logger.info(f"Config name: {config_name}")
        
        if not config_name:
            raise ValidationError('Configuration name is required', 'config_name')
        
        logger.info(f"VPN connection attempt from {request.remote_addr} using config: {config_name}")
        
        result = get_vpn_service().connect_vpn(config_name)
        
        # Log result (without sensitive info)
        if result.success:
            logger.info(f"Successful VPN connection using config: {config_name}")
        else:
            logger.warning(f"Failed VPN connection attempt using config: {config_name}")
        
        return jsonify(result.to_dict())
        
    except (ValidationError, NetworkError) as e:
        logger.error(f"VPN connect error: {e}")
        return jsonify({
            'success': False,
            'error': type(e).__name__.lower(),
            'message': str(e)
        }), 400 if isinstance(e, ValidationError) else 500
    except Exception as e:
        logger.error(f"Unexpected VPN connect error: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500


@api_bp.route('/vpn/disconnect', methods=['POST'])
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_LOW'])
def disconnect_vpn():
    """
    Disconnect from current VPN connection
    
    Returns:
        JSON response with VPN disconnection result
    """
    try:
        logger.info(f"VPN disconnection requested from {request.remote_addr}")
        
        result = get_vpn_service().disconnect_vpn()
        
        # Log result
        if result.success:
            logger.info("Successfully disconnected from VPN")
        else:
            logger.warning("Failed VPN disconnection attempt")
        
        return jsonify(result.to_dict())
        
    except Exception as e:
        logger.error(f"Error disconnecting from VPN: {e}")
        return jsonify({
            'success': False,
            'error': 'vpn_disconnect_error',
            'message': 'Failed to disconnect from VPN'
        }), 500


@api_bp.route('/vpn/configs', methods=['GET'])
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_NORMAL'])
def list_vpn_configs():
    """
    List available VPN configurations
    
    Returns:
        JSON response with list of available VPN configurations
    """
    try:
        status = get_vpn_service().get_vpn_status()
        
        return jsonify({
            'success': True,
            'configs': status.get('available_configs', []),
            'count': len(status.get('available_configs', []))
        })
        
    except Exception as e:
        logger.error(f"Error listing VPN configs: {e}")
        return jsonify({
            'success': False,
            'error': 'vpn_list_error',
            'message': 'Failed to list VPN configurations'
        }), 500


@api_bp.route('/vpn/configs', methods=['POST'])
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_CRITICAL'])
@security_manager.validate_input('json')
def upload_vpn_config():
    """
    Upload a new VPN configuration
    
    Request Body:
        {
            "config_name": "home_server",
            "config_content": "[Interface]\nPrivateKey = ...\n[Peer]\nPublicKey = ..."
        }
    
    Returns:
        JSON response with upload result
    """
    try:
        data = request.get_json()
        config_name = data.get('config_name')
        config_content = data.get('config_content')
        
        if not config_name:
            raise ValidationError('Configuration name is required', 'config_name')
        
        if not config_content:
            raise ValidationError('Configuration content is required', 'config_content')
        
        logger.info(f"VPN config upload requested from {request.remote_addr} for: {config_name}")
        
        result = get_vpn_service().upload_config(config_name, config_content)
        
        # Log result
        if result.success:
            logger.info(f"Successfully uploaded VPN config: {config_name}")
        else:
            logger.warning(f"Failed to upload VPN config: {config_name}")
        
        return jsonify(result.to_dict())
        
    except (ValidationError, NetworkError) as e:
        return jsonify({
            'success': False,
            'error': type(e).__name__.lower(),
            'message': str(e)
        }), 400 if isinstance(e, ValidationError) else 500


@api_bp.route('/vpn/configs/<config_name>', methods=['DELETE'])
@security_manager.rate_limit(max_requests=lambda: current_app.config['RATE_LIMIT_CRITICAL'])
def delete_vpn_config(config_name):
    """
    Delete a VPN configuration
    
    Args:
        config_name: Name of the configuration to delete
    
    Returns:
        JSON response with deletion result
    """
    try:
        if not config_name:
            raise ValidationError('Configuration name is required', 'config_name')
        
        logger.info(f"VPN config deletion requested from {request.remote_addr} for: {config_name}")
        
        result = get_vpn_service().delete_config(config_name)
        
        # Log result
        if result.success:
            logger.info(f"Successfully deleted VPN config: {config_name}")
        else:
            logger.warning(f"Failed to delete VPN config: {config_name}")
        
        return jsonify(result.to_dict())
        
    except (ValidationError, NetworkError) as e:
        return jsonify({
            'success': False,
            'error': type(e).__name__.lower(),
            'message': str(e)
        }), 400 if isinstance(e, ValidationError) else 500