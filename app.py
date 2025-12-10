"""
TravelNet Portal - Professional Travel Router Management Application
"""
import logging
import subprocess
import json
import qrcode
import io
import base64
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file upload

class NetworkManager:
    """Handles all network-related operations"""
    
    @staticmethod
    def scan_wifi_networks():
        """Scan for available WiFi networks"""
        try:
            result = subprocess.run(
                ['nmcli', '--colors', 'no', '-t', '-f', 'SSID,SECURITY,SIGNAL', 'dev', 'wifi', 'list', 'ifname', config.WIFI_INTERFACE],
                capture_output=True, text=True, timeout=30
            )
            
            networks = []
            for line in result.stdout.strip().split('\n'):
                if line and ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 3 and parts[0]:  # Ensure SSID is not empty
                        networks.append({
                            'ssid': parts[0],
                            'security': parts[1] if parts[1] else 'Open',
                            'signal': int(parts[2]) if parts[2].isdigit() else 0
                        })
            
            # Sort by signal strength
            networks.sort(key=lambda x: x['signal'], reverse=True)
            return networks
            
        except subprocess.TimeoutExpired:
            logger.error("WiFi scan timed out")
            return []
        except Exception as e:
            logger.error(f"Error scanning WiFi networks: {e}")
            return []
    
    @staticmethod
    def connect_to_wifi(ssid, password=None):
        """Connect to a WiFi network"""
        try:
            cmd = ['nmcli', '--colors', 'no', 'device', 'wifi', 'connect', ssid, 'ifname', config.WIFI_INTERFACE]
            if password:
                cmd.extend(['password', password])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"Successfully connected to {ssid}")
                return {'success': True, 'message': f'Connected to {ssid}'}
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                logger.error(f"Failed to connect to {ssid}: {error_msg}")
                return {'success': False, 'message': f'Failed to connect: {error_msg}'}
                
        except subprocess.TimeoutExpired:
            return {'success': False, 'message': 'Connection attempt timed out'}
        except Exception as e:
            logger.error(f"Error connecting to WiFi: {e}")
            return {'success': False, 'message': f'Connection error: {str(e)}'}
    
    @staticmethod
    def get_connection_status():
        """Get current network connection status"""
        try:
            result = subprocess.run(
                ['nmcli', '--colors', 'no', '-t', '-f', 'DEVICE,STATE,CONNECTION', 'device', 'status'],
                capture_output=True, text=True, timeout=10
            )
            
            status = {}
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(':')
                    if len(parts) >= 3:
                        device = parts[0]
                        state = parts[1]
                        connection = parts[2] if parts[2] else 'Not connected'
                        status[device] = {'state': state, 'connection': connection}
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting connection status: {e}")
            return {}

class SystemManager:
    """Handles system-related operations"""
    
    @staticmethod
    def reboot_system():
        """Reboot the system"""
        try:
            subprocess.run(['sudo', 'reboot'], timeout=5)
            return {'success': True, 'message': 'System reboot initiated'}
        except Exception as e:
            logger.error(f"Error rebooting system: {e}")
            return {'success': False, 'message': f'Reboot failed: {str(e)}'}
    
    @staticmethod
    def manage_ssh(action):
        """Enable, disable, or check SSH status"""
        try:
            if action == 'enable':
                subprocess.run(['sudo', 'systemctl', 'enable', 'ssh'], timeout=10)
                subprocess.run(['sudo', 'systemctl', 'start', 'ssh'], timeout=10)
                return {'success': True, 'message': 'SSH enabled and started'}
            elif action == 'disable':
                subprocess.run(['sudo', 'systemctl', 'stop', 'ssh'], timeout=10)
                return {'success': True, 'message': 'SSH stopped'}
            elif action == 'status':
                result = subprocess.run(['sudo', 'systemctl', 'is-active', 'ssh'], 
                                      capture_output=True, text=True, timeout=10)
                is_active = result.stdout.strip() == 'active'
                return {'success': True, 'active': is_active}
        except Exception as e:
            logger.error(f"Error managing SSH: {e}")
            return {'success': False, 'message': f'SSH operation failed: {str(e)}'}

# Initialize managers
network_manager = NetworkManager()
system_manager = SystemManager()

@app.route('/')
def index():
    """Main dashboard"""
    try:
        networks = network_manager.scan_wifi_networks()
        connection_status = network_manager.get_connection_status()
        ssh_status = system_manager.manage_ssh('status')
        
        return render_template('index.html', 
                             app_name=config.APP_NAME,
                             networks=networks,
                             connection_status=connection_status,
                             ssh_active=ssh_status.get('active', False))
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash('Error loading dashboard', 'error')
        return render_template('error.html', error=str(e))

@app.route('/connect', methods=['POST'])
def connect_wifi():
    """Connect to WiFi network"""
    try:
        data = request.get_json()
        ssid = data.get('ssid')
        password = data.get('password', '')
        
        if not ssid:
            return jsonify({'success': False, 'message': 'SSID is required'})
        
        result = network_manager.connect_to_wifi(ssid, password if password else None)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in connect_wifi: {e}")
        return jsonify({'success': False, 'message': f'Connection error: {str(e)}'})

@app.route('/scan')
def scan_networks():
    """Scan for WiFi networks"""
    try:
        networks = network_manager.scan_wifi_networks()
        return jsonify({'success': True, 'networks': networks})
    except Exception as e:
        logger.error(f"Error scanning networks: {e}")
        return jsonify({'success': False, 'message': f'Scan error: {str(e)}'})

@app.route('/status')
def get_status():
    """Get system and network status"""
    try:
        connection_status = network_manager.get_connection_status()
        ssh_status = system_manager.manage_ssh('status')
        
        return jsonify({
            'success': True,
            'connection_status': connection_status,
            'ssh_active': ssh_status.get('active', False),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'success': False, 'message': f'Status error: {str(e)}'})

@app.route('/system/<action>', methods=['POST'])
def system_action(action):
    """Handle system actions (reboot, SSH management)"""
    try:
        if action == 'reboot':
            result = system_manager.reboot_system()
        elif action in ['ssh_enable', 'ssh_disable']:
            ssh_action = 'enable' if action == 'ssh_enable' else 'disable'
            result = system_manager.manage_ssh(ssh_action)
        else:
            return jsonify({'success': False, 'message': 'Invalid action'})
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in system action {action}: {e}")
        return jsonify({'success': False, 'message': f'System action failed: {str(e)}'})

@app.route('/qr-connect')
def qr_connect_page():
    """QR code connection page"""
    return render_template('qr_connect.html', app_name=config.APP_NAME)

@app.route('/generate-qr', methods=['POST'])
def generate_qr():
    """Generate QR code for WiFi connection"""
    try:
        data = request.get_json()
        ssid = data.get('ssid')
        password = data.get('password', '')
        security = data.get('security', 'WPA')
        
        if not ssid:
            return jsonify({'success': False, 'message': 'SSID is required'})
        
        # Create WiFi QR code string
        if security.upper() == 'OPEN' or not password:
            wifi_string = f"WIFI:T:nopass;S:{ssid};;"
        else:
            wifi_string = f"WIFI:T:{security};S:{ssid};P:{password};;"
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(wifi_string)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for web display
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'qr_code': f'data:image/png;base64,{img_base64}',
            'wifi_string': wifi_string
        })
        
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        return jsonify({'success': False, 'message': f'QR generation failed: {str(e)}'})

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error='Internal server error'), 500

if __name__ == '__main__':
    logger.info(f"Starting {config.APP_NAME} v{config.APP_VERSION}")
    app.run(debug=False, host='0.0.0.0', port=80)