"""
Network Service Module

Business logic for WiFi network operations including scanning,
connection management, and status monitoring.
"""

import subprocess
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from flask import current_app

from app.core.errors import NetworkError, ValidationError
from app.core.security import security_manager

logger = logging.getLogger(__name__)


@dataclass
class NetworkInfo:
    """Data class for network information"""
    ssid: str
    security: str
    signal_strength: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'ssid': self.ssid,
            'security': self.security,
            'signal_strength': self.signal_strength
        }


@dataclass
class ConnectionResult:
    """Data class for connection results"""
    success: bool
    message: str
    details: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            'success': self.success,
            'message': self.message
        }
        if self.details:
            result['details'] = self.details
        return result


class NetworkService:
    """Service class for network operations"""
    
    def __init__(self):
        self.wifi_interface = current_app.config['WIFI_INTERFACE']
        self.ap_interface = current_app.config['AP_INTERFACE']
        self.default_ap_ssid = current_app.config['DEFAULT_AP_SSID']
    
    def scan_wifi_networks(self) -> List[NetworkInfo]:
        """
        Scan for available WiFi networks
        
        Returns:
            List of NetworkInfo objects
            
        Raises:
            NetworkError: If scanning fails
        """
        try:
            logger.info("Starting WiFi network scan")
            
            result = subprocess.run(
                ['nmcli', '--colors', 'no', '-t', '-f', 'SSID,SECURITY,SIGNAL', 
                 'dev', 'wifi', 'list', 'ifname', self.wifi_interface],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                raise NetworkError(f"Network scan failed: {result.stderr}")
            
            networks = []
            seen_networks = {}  # Track networks by SSID to avoid duplicates
            
            for line in result.stdout.strip().split('\n'):
                if line and ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 3 and parts[0]:
                        ssid = parts[0].strip()
                        
                        # Filter out empty SSIDs
                        if ssid:
                            try:
                                signal = int(parts[2]) if parts[2].isdigit() else 0
                                security = parts[1].strip() if parts[1] else 'Open'
                                
                                # Only keep the strongest signal for each SSID
                                if ssid not in seen_networks or signal > seen_networks[ssid].signal_strength:
                                    seen_networks[ssid] = NetworkInfo(
                                        ssid=ssid,
                                        security=security,
                                        signal_strength=signal
                                    )
                            except (ValueError, IndexError) as e:
                                logger.warning(f"Error parsing network data: {e}")
                                continue
            
            # Convert to list and sort by signal strength
            networks = list(seen_networks.values())
            networks.sort(key=lambda x: x.signal_strength, reverse=True)
            
            logger.info(f"Found {len(networks)} unique networks")
            return networks
            
        except subprocess.TimeoutExpired:
            logger.error("WiFi scan timed out")
            raise NetworkError("Network scan timed out. Please try again.")
        except Exception as e:
            logger.error(f"Error scanning WiFi networks: {e}")
            raise NetworkError("Failed to scan for networks. Please check your WiFi adapter.")
    
    def connect_to_wifi(self, ssid: str, password: Optional[str] = None) -> ConnectionResult:
        """
        Connect to a WiFi network
        
        Args:
            ssid: Network SSID
            password: Network password (optional for open networks)
            
        Returns:
            ConnectionResult object
            
        Raises:
            ValidationError: If input validation fails
            NetworkError: If connection fails
        """
        try:
            # Input validation
            sanitized_ssid = security_manager.sanitize_ssid(ssid)
            if not sanitized_ssid:
                raise ValidationError('Invalid SSID format', 'ssid')
            
            # Validate password if provided
            if password and not security_manager._validate_password(password):
                raise ValidationError('Invalid password format or length', 'password')
            
            logger.info(f"Attempting to connect to network: {sanitized_ssid}")
            
            # First, try to connect using existing saved connection profile
            if not password or password.strip() == '':
                logger.info(f"Trying to connect using saved profile for {sanitized_ssid}")
                result = self._try_saved_connection(sanitized_ssid)
                if result.success:
                    return result
                logger.info("No saved profile found or failed, creating new connection")
            
            # Delete any existing connection with the same name for fresh connection
            self._delete_existing_connection(sanitized_ssid)
            
            # Build connection command
            cmd = self._build_connection_command(sanitized_ssid, password)
            
            # Execute connection command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            
            if result.returncode == 0:
                logger.info(f"Successfully connected to {sanitized_ssid}")
                return ConnectionResult(
                    success=True,
                    message=f'Successfully connected to {sanitized_ssid}',
                    details=result.stdout.strip()
                )
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                logger.error(f"Failed to connect to {sanitized_ssid}: {error_msg}")
                return ConnectionResult(
                    success=False,
                    message=self._parse_connection_error(error_msg)
                )
                
        except subprocess.TimeoutExpired:
            logger.error(f"Connection to {sanitized_ssid} timed out")
            return ConnectionResult(
                success=False,
                message="Connection attempt timed out. Please try again."
            )
        except (ValidationError, NetworkError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to WiFi: {e}")
            raise NetworkError("An unexpected error occurred during connection.")
    
    def disconnect_from_wifi(self) -> ConnectionResult:
        """
        Disconnect from current WiFi network
        
        Returns:
            ConnectionResult object
            
        Raises:
            NetworkError: If disconnection fails
        """
        try:
            logger.info("Attempting to disconnect from WiFi")
            
            # Get current connection to disconnect from
            status = self.get_connection_status()
            if not status.get('connected') or not status.get('current_network'):
                return ConnectionResult(
                    success=False,
                    message="No active WiFi connection to disconnect from"
                )
            
            current_ssid = status['current_network']['ssid']
            
            # Disconnect using nmcli
            result = subprocess.run(
                ['nmcli', 'device', 'disconnect', self.wifi_interface],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully disconnected from {current_ssid}")
                return ConnectionResult(
                    success=True,
                    message=f'Successfully disconnected from {current_ssid}',
                    details=result.stdout.strip()
                )
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                logger.error(f"Failed to disconnect: {error_msg}")
                return ConnectionResult(
                    success=False,
                    message=self._parse_disconnection_error(error_msg)
                )
                
        except subprocess.TimeoutExpired:
            logger.error("Disconnection timed out")
            return ConnectionResult(
                success=False,
                message="Disconnection attempt timed out. Please try again."
            )
        except Exception as e:
            logger.error(f"Unexpected error disconnecting from WiFi: {e}")
            return ConnectionResult(
                success=False,
                message="An unexpected error occurred during disconnection."
            )
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get current network connection status
        
        Returns:
            Dictionary with connection status information
        """
        try:
            result = subprocess.run(
                ['nmcli', '--colors', 'no', '-t', '-f', 'DEVICE,STATE,CONNECTION', 'device', 'status'],
                capture_output=True, text=True, timeout=10
            )
            
            status = {}
            current_connection = None
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(':')
                        if len(parts) >= 3:
                            device = parts[0]
                            state = parts[1]
                            connection = parts[2] if parts[2] else None
                            
                            status[device] = {
                                'state': state,
                                'connection': connection
                            }
                            
                            # Check if this is our WiFi interface and it's connected
                            if device == self.wifi_interface and state == 'connected' and connection:
                                # Get actual signal strength and security for current connection
                                signal_strength, security = self._get_current_network_details(connection)
                                current_connection = {
                                    'ssid': connection,
                                    'signal_strength': signal_strength,
                                    'security': security
                                }
            
            return {
                'success': True,
                'connected': current_connection is not None,
                'current_network': current_connection,
                'device_status': status
            }
            
        except Exception as e:
            logger.error(f"Error getting connection status: {e}")
            return {
                'success': False,
                'connected': False,
                'current_network': None,
                'error': str(e)
            }
    
    def _get_current_network_details(self, ssid: str) -> tuple[int, str]:
        """Get signal strength and security for current network"""
        try:
            # Get current network details from scan
            result = subprocess.run(
                ['nmcli', '--colors', 'no', '-t', '-f', 'SSID,SECURITY,SIGNAL', 'dev', 'wifi', 'list', 'ifname', self.wifi_interface],
                capture_output=True, text=True, timeout=15
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(':')
                        if len(parts) >= 3:
                            network_ssid = parts[0].strip()
                            if network_ssid == ssid:
                                security = parts[1].strip() if parts[1] else 'Open'
                                signal = int(parts[2]) if parts[2].isdigit() else -70
                                return signal, security
            
            # Fallback values if not found in scan
            return -60, 'WPA2'
            
        except Exception as e:
            logger.warning(f"Error getting current network details: {e}")
            return -60, 'WPA2'
    
    def _try_saved_connection(self, ssid: str) -> ConnectionResult:
        """Try to connect using existing saved connection profile"""
        try:
            # Try to activate existing connection profile
            result = subprocess.run(
                ['nmcli', 'connection', 'up', ssid, 'ifname', self.wifi_interface],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully connected using saved profile for {ssid}")
                return ConnectionResult(
                    success=True,
                    message=f'Connected to {ssid} using saved credentials',
                    details=result.stdout.strip()
                )
            else:
                logger.debug(f"Failed to use saved profile for {ssid}: {result.stderr}")
                return ConnectionResult(
                    success=False,
                    message="No saved profile available"
                )
                
        except subprocess.TimeoutExpired:
            logger.debug(f"Timeout trying saved connection for {ssid}")
            return ConnectionResult(
                success=False,
                message="Saved connection attempt timed out"
            )
        except Exception as e:
            logger.debug(f"Error trying saved connection for {ssid}: {e}")
            return ConnectionResult(
                success=False,
                message="No saved profile available"
            )
    
    def _delete_existing_connection(self, ssid: str) -> None:
        """Delete existing connection profile"""
        try:
            subprocess.run(
                ['nmcli', 'connection', 'delete', ssid],
                capture_output=True, timeout=10
            )
        except subprocess.TimeoutExpired:
            logger.warning("Timeout while deleting existing connection")
        except Exception as e:
            logger.debug(f"No existing connection to delete: {e}")
    
    def _build_connection_command(self, ssid: str, password: Optional[str]) -> List[str]:
        """Build the nmcli connection command"""
        cmd = ['nmcli', 'device', 'wifi', 'connect', ssid]
        
        if password and password.strip():
            cmd.extend(['password', password.strip()])
        
        cmd.extend(['ifname', self.wifi_interface])
        return cmd
    
    def _parse_connection_error(self, error_msg: str) -> str:
        """Parse connection error message and return user-friendly message"""
        error_lower = error_msg.lower()
        
        if 'secrets were required' in error_lower or 'authentication' in error_lower:
            return 'Authentication failed. Please check the password.'
        elif 'no network with ssid' in error_lower or 'not found' in error_lower:
            return 'Network not found. Please scan for networks again.'
        elif 'already exists' in error_lower:
            return 'Connection profile exists. Retrying...'
        elif 'timeout' in error_lower:
            return 'Connection timed out. Network may be out of range.'
        elif 'device not found' in error_lower:
            return 'WiFi adapter not available.'
        else:
            return 'Connection failed. Please try again.'
    
    def _should_include_network(self, ssid: str) -> bool:
        """Check if a network should be included in the scan results"""
        # Get the current hotspot SSID being broadcast by our AP interface
        current_hotspot_ssid = self._get_current_hotspot_ssid()
        
        # Exclude our own hotspot
        if current_hotspot_ssid and ssid == current_hotspot_ssid:
            logger.debug(f"Filtering out own hotspot: {ssid}")
            return False
            
        # Also exclude the configured default AP SSID as fallback
        if ssid == self.default_ap_ssid:
            logger.debug(f"Filtering out default AP SSID: {ssid}")
            return False
                
        return True
    
    def _get_current_hotspot_ssid(self) -> Optional[str]:
        """Get the SSID of the currently active hotspot on the AP interface"""
        try:
            # Try to get the SSID from the AP interface using iwconfig
            result = subprocess.run(
                ['iwconfig', self.ap_interface],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                # Parse iwconfig output to find ESSID
                for line in result.stdout.split('\n'):
                    if 'ESSID:' in line:
                        # Extract SSID from ESSID:"network_name" format
                        essid_part = line.split('ESSID:')[1].strip()
                        if essid_part.startswith('"') and essid_part.endswith('"'):
                            return essid_part[1:-1]  # Remove quotes
                        elif essid_part != 'off/any':
                            return essid_part
            
            # Fallback: try to get from NetworkManager connections
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'NAME,DEVICE', 'connection', 'show', '--active'],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(':')
                        if len(parts) >= 2 and parts[1] == self.ap_interface:
                            return parts[0]  # Return connection name
                            
        except Exception as e:
            logger.debug(f"Error getting current hotspot SSID: {e}")
            
        return None
    
    def _parse_disconnection_error(self, error_msg: str) -> str:
        """Parse disconnection error message and return user-friendly message"""
        error_lower = error_msg.lower()
        
        if 'not connected' in error_lower or 'no active connection' in error_lower:
            return 'No active connection to disconnect from.'
        elif 'device not found' in error_lower:
            return 'WiFi adapter not available.'
        elif 'timeout' in error_lower:
            return 'Disconnection timed out. Please try again.'
        else:
            return 'Disconnection failed. Please try again.'
    
    def get_hotspot_credentials(self) -> Dict[str, str]:
        """
        Get the actual hotspot SSID and password from system configuration
        
        Returns:
            Dictionary with ssid, password, visible, and enabled keys
        """
        try:
            # Try to read from hostapd configuration
            hostapd_config = '/etc/hostapd/hostapd.conf'
            
            result = subprocess.run(
                ['sudo', 'cat', hostapd_config],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                ssid = None
                password = None
                hidden = False
                
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line.startswith('ssid='):
                        ssid = line.split('=', 1)[1]
                    elif line.startswith('wpa_passphrase='):
                        password = line.split('=', 1)[1]
                    elif line.startswith('ignore_broadcast_ssid='):
                        hidden = line.split('=', 1)[1] == '1'
                
                if ssid:
                    logger.info(f"Found hotspot configuration: SSID={ssid[:10]}...")
                    return {
                        'ssid': ssid,
                        'password': password or '',
                        'security': 'WPA' if password else 'Open',
                        'visible': not hidden,
                        'enabled': True  # If config exists, assume enabled
                    }
            
            # Fallback: try to get from NetworkManager
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'NAME,TYPE,DEVICE', 'connection', 'show', '--active'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(':')
                        if len(parts) >= 3 and parts[2] == self.ap_interface:
                            # Found active connection on AP interface
                            connection_name = parts[0]
                            
                            # Try to get the password for this connection
                            password_result = subprocess.run(
                                ['sudo', 'nmcli', '-s', '-g', '802-11-wireless-security.psk', 
                                 'connection', 'show', connection_name],
                                capture_output=True, text=True, timeout=10
                            )
                            
                            password = password_result.stdout.strip() if password_result.returncode == 0 else ''
                            
                            logger.info(f"Found NetworkManager hotspot: SSID={connection_name[:10]}...")
                            return {
                                'ssid': connection_name,
                                'password': password,
                                'security': 'WPA' if password else 'Open',
                                'visible': True,  # Default to visible
                                'enabled': True
                            }
            
            # Final fallback to config defaults
            logger.warning("Could not detect actual hotspot configuration, using defaults")
            return {
                'ssid': self.default_ap_ssid,
                'password': current_app.config['DEFAULT_AP_PASSWORD'],
                'security': 'WPA',
                'visible': True,
                'enabled': True
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout getting hotspot configuration")
            return {
                'ssid': self.default_ap_ssid,
                'password': current_app.config['DEFAULT_AP_PASSWORD'],
                'security': 'WPA',
                'visible': True,
                'enabled': True
            }
        except Exception as e:
            logger.error(f"Error getting hotspot configuration: {e}")
            return {
                'ssid': self.default_ap_ssid,
                'password': current_app.config['DEFAULT_AP_PASSWORD'],
                'security': 'WPA',
                'visible': True,
                'enabled': True
            }
    
    def update_hotspot_config(self, ssid: str, password: str = '', visible: bool = True, enabled: bool = True) -> ConnectionResult:
        """
        Update hotspot configuration
        
        Args:
            ssid: New hotspot SSID
            password: New hotspot password (empty for open network)
            visible: Whether hotspot should be visible
            enabled: Whether hotspot should be enabled
            
        Returns:
            ConnectionResult object
        """
        try:
            # Input validation
            from app.core.security import security_manager
            sanitized_ssid = security_manager.sanitize_ssid(ssid)
            if not sanitized_ssid:
                raise ValidationError('Invalid SSID format', 'ssid')
            
            if password and not security_manager._validate_password(password):
                raise ValidationError('Invalid password format or length', 'password')
            
            logger.info(f"Updating hotspot configuration: SSID={sanitized_ssid}")
            
            # First, try to update using NetworkManager
            result = self._update_nm_hotspot(sanitized_ssid, password, visible, enabled)
            if result.success:
                return result
            
            # Fallback: try to update hostapd configuration
            return self._update_hostapd_config(sanitized_ssid, password, visible, enabled)
            
        except (ValidationError, NetworkError):
            raise
        except Exception as e:
            logger.error(f"Error updating hotspot configuration: {e}")
            return ConnectionResult(
                success=False,
                message='Failed to update hotspot configuration'
            )
    
    def _update_nm_hotspot(self, ssid: str, password: str, visible: bool, enabled: bool) -> ConnectionResult:
        """Update hotspot using NetworkManager"""
        try:
            # Check if hotspot connection exists
            result = subprocess.run(
                ['nmcli', 'connection', 'show', ssid],
                capture_output=True, text=True, timeout=10
            )
            
            connection_exists = result.returncode == 0
            
            if enabled:
                if connection_exists:
                    # Modify existing connection
                    cmd = ['sudo', 'nmcli', 'connection', 'modify', ssid]
                    cmd.extend(['802-11-wireless.ssid', ssid])
                    
                    if password:
                        cmd.extend(['802-11-wireless-security.key-mgmt', 'wpa-psk'])
                        cmd.extend(['802-11-wireless-security.psk', password])
                    else:
                        cmd.extend(['802-11-wireless-security.key-mgmt', ''])
                        cmd.extend(['802-11-wireless-security.psk', ''])
                    
                    # Set visibility
                    cmd.extend(['802-11-wireless.hidden', 'false' if visible else 'true'])
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                    
                    if result.returncode != 0:
                        logger.error(f"Failed to modify hotspot connection: {result.stderr}")
                        return ConnectionResult(
                            success=False,
                            message='Failed to update hotspot settings'
                        )
                else:
                    # Create new hotspot connection
                    cmd = ['sudo', 'nmcli', 'connection', 'add', 'type', 'wifi', 'ifname', self.ap_interface]
                    cmd.extend(['con-name', ssid, 'autoconnect', 'yes', 'wifi.mode', 'ap'])
                    cmd.extend(['wifi.ssid', ssid])
                    cmd.extend(['ipv4.method', 'shared'])
                    
                    if password:
                        cmd.extend(['wifi-sec.key-mgmt', 'wpa-psk', 'wifi-sec.psk', password])
                    
                    # Set visibility
                    if not visible:
                        cmd.extend(['wifi.hidden', 'true'])
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                    
                    if result.returncode != 0:
                        logger.error(f"Failed to create hotspot connection: {result.stderr}")
                        return ConnectionResult(
                            success=False,
                            message='Failed to create hotspot configuration'
                        )
                
                # Activate the connection
                result = subprocess.run(
                    ['sudo', 'nmcli', 'connection', 'up', ssid],
                    capture_output=True, text=True, timeout=20
                )
                
                if result.returncode == 0:
                    logger.info(f"Hotspot {ssid} activated successfully")
                    return ConnectionResult(
                        success=True,
                        message=f'Hotspot "{ssid}" configured and activated successfully'
                    )
                else:
                    logger.error(f"Failed to activate hotspot: {result.stderr}")
                    return ConnectionResult(
                        success=False,
                        message='Hotspot configured but failed to activate'
                    )
            else:
                # Disable hotspot
                if connection_exists:
                    result = subprocess.run(
                        ['sudo', 'nmcli', 'connection', 'down', ssid],
                        capture_output=True, text=True, timeout=15
                    )
                    
                    if result.returncode == 0:
                        return ConnectionResult(
                            success=True,
                            message='Hotspot disabled successfully'
                        )
                    else:
                        return ConnectionResult(
                            success=False,
                            message='Failed to disable hotspot'
                        )
                else:
                    return ConnectionResult(
                        success=True,
                        message='Hotspot is already disabled'
                    )
                    
        except subprocess.TimeoutExpired:
            logger.error("Timeout updating NetworkManager hotspot")
            return ConnectionResult(
                success=False,
                message='Hotspot update timed out'
            )
        except Exception as e:
            logger.error(f"Error updating NetworkManager hotspot: {e}")
            return ConnectionResult(
                success=False,
                message='Failed to update hotspot via NetworkManager'
            )
    
    def _update_hostapd_config(self, ssid: str, password: str, visible: bool, enabled: bool) -> ConnectionResult:
        """Update hotspot using hostapd configuration (fallback method)"""
        try:
            logger.info("Attempting to update hotspot via hostapd configuration")
            
            # This is a simplified implementation - in a real scenario you'd want to
            # properly parse and update the hostapd.conf file
            return ConnectionResult(
                success=False,
                message='Hostapd configuration update not implemented. Please use NetworkManager.'
            )
            
        except Exception as e:
            logger.error(f"Error updating hostapd configuration: {e}")
            return ConnectionResult(
                success=False,
                message='Failed to update hostapd configuration'
            )