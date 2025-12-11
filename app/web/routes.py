"""
Web Interface Routes Module

Web interface routes for the TravelNet Portal dashboard and pages.
Handles both regular web requests and captive portal detection.
"""

import logging
from flask import Blueprint, render_template, request, redirect, current_app

from app.core.security import security_manager
from app.services.network_service import NetworkService
from app.services.system_service import SystemService
from app.services.vpn_service import VPNService

logger = logging.getLogger(__name__)

# Create web blueprint
web_bp = Blueprint('web', __name__)

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

def get_vpn_service():
    """Get VPN service instance"""
    if not hasattr(current_app, 'vpn_service'):
        current_app.vpn_service = VPNService()
    return current_app.vpn_service


@web_bp.route('/')
@security_manager.rate_limit(max_requests=100)
def index():
    """
    Main dashboard page
    
    Handles both regular dashboard access and captive portal detection
    """
    try:
        # Check if this is a captive portal detection request
        user_agent = request.headers.get('User-Agent', '').lower()
        host = request.headers.get('Host', '')
        
        # Common captive portal detection patterns
        captive_patterns = [
            'captivenetworksupport',
            'wispr',
            'connectivitycheck',
            'networkcheck',
            'internet-check'
        ]
        
        # Check if this is a captive portal request
        is_captive_request = (
            any(pattern in user_agent for pattern in captive_patterns) or
            host not in current_app.config['ALLOWED_HOSTS']
        )
        
        if is_captive_request:
            logger.info(f"Captive portal request from {request.remote_addr}, host: {host}")
            return render_template('captive_portal.html', 
                                 app_name=current_app.config['APP_NAME'])
        
        # Regular dashboard access
        logger.info(f"Dashboard access from {request.remote_addr}")
        
        # Get network and system information
        try:
            networks = get_network_service().scan_wifi_networks()
            connection_status = get_network_service().get_connection_status()
            system_status = get_system_service().get_system_status()
            vpn_status = get_vpn_service().get_vpn_status()
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            networks = []
            connection_status = {'connected': False}
            system_status = {'success': True}
            vpn_status = {'connected': False, 'available_configs': []}
        
        # Get current connection info for highlighting
        current_ssid = None
        if connection_status.get('connected') and connection_status.get('current_network'):
            current_ssid = connection_status['current_network']['ssid']
        
        return render_template('index.html',
                             app_name=current_app.config['APP_NAME'],
                             networks=[network.to_dict() for network in networks],
                             connection_status=connection_status,
                             system_status=system_status,
                             vpn_status=vpn_status,
                             current_ssid=current_ssid,
                             features={
                                 'ssh_management': current_app.config['ENABLE_SSH_MANAGEMENT'],
                                 'system_reboot': current_app.config['ENABLE_SYSTEM_REBOOT'],
                                 'qr_generation': current_app.config['ENABLE_QR_GENERATION'],
                                 'vpn_tunnel': True
                             })
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('error.html', 
                             error='Dashboard Error',
                             message='Failed to load dashboard. Please try again.'), 500


@web_bp.route('/qr-connect')
@security_manager.rate_limit(max_requests=50)
def qr_connect_page():
    """QR code generation page"""
    if not current_app.config['ENABLE_QR_GENERATION']:
        return render_template('error.html',
                             error='Feature Disabled',
                             message='QR code generation is not enabled.'), 403
    
    return render_template('qr_connect.html', 
                         app_name=current_app.config['APP_NAME'])


# Captive portal detection endpoints
@web_bp.route('/generate_204')
@web_bp.route('/gen_204')
@web_bp.route('/ncsi.txt')
@web_bp.route('/hotspot-detect.html')
@web_bp.route('/connectivity-check.html')
@web_bp.route('/check_network_status.txt')
@web_bp.route('/library/test/success.html')
@web_bp.route('/captive')
def captive_portal_detection():
    """Captive portal detection endpoints - redirect to main portal"""
    logger.info(f"Captive portal detection request from {request.remote_addr} for {request.url}")
    return redirect('http://192.168.4.1/', code=302)


@web_bp.route('/apple-captive-portal')
def apple_captive_portal():
    """Apple-specific captive portal detection"""
    logger.info(f"Apple captive portal request from {request.remote_addr}")
    return render_template('captive_portal.html', 
                         app_name=current_app.config['APP_NAME'])


@web_bp.route('/bag')
@web_bp.route('/bag/')
def apple_bag():
    """Apple bag endpoint for connectivity checks"""
    logger.info(f"Apple bag request from {request.remote_addr}")
    return "Captive Portal", 200


@web_bp.route('/redirect')
def captive_redirect():
    """Handle captive portal redirects with original URL"""
    original_url = request.args.get('url', '')
    logger.info(f"Captive portal redirect request for: {original_url}")
    return redirect('http://192.168.4.1/', code=302)


@web_bp.route('/success.txt')
@web_bp.route('/success.html')
def captive_success():
    """Handle success pages for captive portal detection"""
    return "Success", 200


# Legacy API routes for JavaScript compatibility
@web_bp.route('/connect', methods=['POST'])
@security_manager.rate_limit(max_requests=5)
def connect_wifi():
    """Legacy WiFi connection endpoint"""
    try:
        data = request.get_json()
        ssid = data.get('ssid')
        password = data.get('password', '')
        
        result = get_network_service().connect_to_wifi(ssid, password if password else None)
        return result.to_dict()
        
    except Exception as e:
        logger.error(f"Error in connect route: {e}")
        return {'success': False, 'message': 'Connection failed'}, 500


@web_bp.route('/scan', methods=['GET'])
@security_manager.rate_limit(max_requests=10)
def scan_networks():
    """Legacy network scanning endpoint"""
    try:
        networks = get_network_service().scan_wifi_networks()
        return {
            'success': True,
            'networks': [network.to_dict() for network in networks]
        }
        
    except Exception as e:
        logger.error(f"Error in scan route: {e}")
        return {'success': False, 'message': 'Scan failed'}, 500

@web_bp.route('/vpn-tunnel')
@security_manager.rate_limit(max_requests=50)
def vpn_tunnel_page():
    """VPN tunnel management page"""
    try:
        vpn_status = get_vpn_service().get_vpn_status()
        return render_template('vpn_tunnel.html', 
                             app_name=current_app.config['APP_NAME'],
                             vpn_status=vpn_status)
    except Exception as e:
        logger.error(f"Error loading VPN tunnel page: {e}")
        return render_template('error.html', 
                             error='VPN Error',
                             message='Failed to load VPN tunnel page. Please try again.'), 500