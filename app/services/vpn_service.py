"""
VPN Service Module

Business logic for VPN tunnel operations including WireGuard connection
management, configuration handling, and status monitoring.
"""

import subprocess
import logging
import os
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from flask import current_app

from app.core.errors import NetworkError, ValidationError
from app.core.security import security_manager

logger = logging.getLogger(__name__)


@dataclass
class VPNConfig:
    """Data class for VPN configuration information"""
    name: str
    interface: str
    status: str
    endpoint: Optional[str] = None
    allowed_ips: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'interface': self.interface,
            'status': self.status,
            'endpoint': self.endpoint,
            'allowed_ips': self.allowed_ips
        }


@dataclass
class VPNResult:
    """Data class for VPN operation results"""
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


class VPNService:
    """Service class for VPN operations"""
    
    def __init__(self):
        # Use absolute path for VPN configs directory
        if hasattr(current_app, 'config') and 'BASE_DIR' in current_app.config:
            self.vpn_configs_dir = Path(current_app.config['BASE_DIR']) / 'vpn_configs'
        else:
            # Fallback to /opt/travelnet/vpn_configs
            self.vpn_configs_dir = Path('/opt/travelnet/vpn_configs')
        
        self.vpn_configs_dir.mkdir(exist_ok=True)
        self.wg_interface_prefix = 'wg'
    
    def get_vpn_status(self) -> Dict[str, Any]:
        """
        Get current VPN connection status
        
        Returns:
            Dictionary with VPN status information
        """
        try:
            # Check if WireGuard is installed
            wg_installed = self._check_wireguard_installed()
            if not wg_installed:
                return {
                    'success': False,
                    'connected': False,
                    'error': 'WireGuard not installed',
                    'configs': []
                }
            
            # Get active WireGuard interfaces
            active_interfaces = self._get_active_wireguard_interfaces()
            
            # Get available configurations
            available_configs = self._get_available_configs()
            
            # Determine if any VPN is connected
            connected = len(active_interfaces) > 0
            current_connection = None
            
            if connected and active_interfaces:
                # Get details of the first active connection
                interface_name = active_interfaces[0]['interface']
                current_connection = {
                    'interface': interface_name,
                    'status': 'connected',
                    'config_name': self._get_config_name_for_interface(interface_name)
                }
                
                # Get connection details
                details = self._get_interface_details(interface_name)
                if details:
                    current_connection.update(details)
            
            return {
                'success': True,
                'connected': connected,
                'current_connection': current_connection,
                'active_interfaces': active_interfaces,
                'available_configs': available_configs,
                'wireguard_installed': wg_installed
            }
            
        except Exception as e:
            logger.error(f"Error getting VPN status: {e}")
            return {
                'success': False,
                'connected': False,
                'error': str(e),
                'configs': []
            }
    
    def connect_vpn(self, config_name: str) -> VPNResult:
        """
        Connect to VPN using specified configuration
        
        Args:
            config_name: Name of the VPN configuration
            
        Returns:
            VPNResult object
        """
        try:
            # Validate config name
            if not self._validate_config_name(config_name):
                raise ValidationError('Invalid configuration name', 'config_name')
            
            config_path = self.vpn_configs_dir / f"{config_name}.conf"
            if not config_path.exists():
                return VPNResult(
                    success=False,
                    message=f"Configuration '{config_name}' not found"
                )
            
            # Check if WireGuard is installed
            if not self._check_wireguard_installed():
                return VPNResult(
                    success=False,
                    message="WireGuard is not installed. Please install it first."
                )
            
            # Disconnect any existing VPN connections
            self._disconnect_all_vpn()
            
            # Generate interface name
            interface_name = f"{self.wg_interface_prefix}0"
            
            logger.info(f"Connecting to VPN using config: {config_name}")
            
            # Copy config to system location temporarily
            system_config_path = f"/etc/wireguard/{interface_name}.conf"
            
            # Copy our config to the system location
            copy_result = subprocess.run(
                ['sudo', 'cp', str(config_path), system_config_path],
                capture_output=True, text=True, timeout=10
            )
            
            if copy_result.returncode != 0:
                logger.error(f"Failed to copy config to system location: {copy_result.stderr}")
                return VPNResult(
                    success=False,
                    message="Failed to prepare VPN configuration"
                )
            
            # Set proper permissions
            subprocess.run(
                ['sudo', 'chmod', '600', system_config_path],
                capture_output=True, timeout=5
            )
            
            # Bring up the WireGuard interface using interface name
            result = subprocess.run(
                ['sudo', 'wg-quick', 'up', interface_name],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully connected to VPN: {config_name}")
                return VPNResult(
                    success=True,
                    message=f"Successfully connected to VPN '{config_name}'",
                    details=result.stdout.strip()
                )
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                logger.error(f"Failed to connect to VPN {config_name}: {error_msg}")
                return VPNResult(
                    success=False,
                    message=self._parse_vpn_error(error_msg)
                )
                
        except subprocess.TimeoutExpired:
            logger.error(f"VPN connection to {config_name} timed out")
            return VPNResult(
                success=False,
                message="VPN connection attempt timed out. Please try again."
            )
        except (ValidationError, NetworkError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to VPN: {e}")
            return VPNResult(
                success=False,
                message="An unexpected error occurred during VPN connection."
            )
    
    def disconnect_vpn(self, interface_name: Optional[str] = None) -> VPNResult:
        """
        Disconnect from VPN
        
        Args:
            interface_name: Specific interface to disconnect (optional)
            
        Returns:
            VPNResult object
        """
        try:
            if interface_name:
                # Disconnect specific interface
                return self._disconnect_interface(interface_name)
            else:
                # Disconnect all VPN connections
                return self._disconnect_all_vpn()
                
        except Exception as e:
            logger.error(f"Unexpected error disconnecting VPN: {e}")
            return VPNResult(
                success=False,
                message="An unexpected error occurred during VPN disconnection."
            )
    
    def upload_config(self, config_name: str, config_content: str) -> VPNResult:
        """
        Upload and validate a VPN configuration
        
        Args:
            config_name: Name for the configuration
            config_content: WireGuard configuration content
            
        Returns:
            VPNResult object
        """
        try:
            # Validate config name
            if not self._validate_config_name(config_name):
                raise ValidationError('Invalid configuration name', 'config_name')
            
            # Validate configuration content
            if not self._validate_wireguard_config(config_content):
                return VPNResult(
                    success=False,
                    message="Invalid WireGuard configuration format"
                )
            
            # Save configuration file
            config_path = self.vpn_configs_dir / f"{config_name}.conf"
            
            # Set secure permissions before writing
            config_path.touch(mode=0o600)
            config_path.write_text(config_content)
            
            logger.info(f"Successfully uploaded VPN config: {config_name}")
            return VPNResult(
                success=True,
                message=f"Configuration '{config_name}' uploaded successfully"
            )
            
        except (ValidationError, NetworkError):
            raise
        except Exception as e:
            logger.error(f"Error uploading VPN config: {e}")
            return VPNResult(
                success=False,
                message="Failed to upload configuration"
            )
    
    def delete_config(self, config_name: str) -> VPNResult:
        """
        Delete a VPN configuration
        
        Args:
            config_name: Name of the configuration to delete
            
        Returns:
            VPNResult object
        """
        try:
            if not self._validate_config_name(config_name):
                raise ValidationError('Invalid configuration name', 'config_name')
            
            config_path = self.vpn_configs_dir / f"{config_name}.conf"
            if not config_path.exists():
                return VPNResult(
                    success=False,
                    message=f"Configuration '{config_name}' not found"
                )
            
            # Check if this config is currently active
            status = self.get_vpn_status()
            if (status.get('connected') and 
                status.get('current_connection', {}).get('config_name') == config_name):
                return VPNResult(
                    success=False,
                    message="Cannot delete active VPN configuration. Disconnect first."
                )
            
            # Delete the configuration file
            config_path.unlink()
            
            logger.info(f"Successfully deleted VPN config: {config_name}")
            return VPNResult(
                success=True,
                message=f"Configuration '{config_name}' deleted successfully"
            )
            
        except (ValidationError, NetworkError):
            raise
        except Exception as e:
            logger.error(f"Error deleting VPN config: {e}")
            return VPNResult(
                success=False,
                message="Failed to delete configuration"
            )
    
    def _check_wireguard_installed(self) -> bool:
        """Check if WireGuard is installed and available"""
        try:
            result = subprocess.run(
                ['which', 'wg'],
                capture_output=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _get_active_wireguard_interfaces(self) -> List[Dict[str, Any]]:
        """Get list of active WireGuard interfaces"""
        try:
            result = subprocess.run(
                ['sudo', 'wg', 'show'],
                capture_output=True, text=True, timeout=10
            )
            
            interfaces = []
            if result.returncode == 0 and result.stdout.strip():
                current_interface = None
                
                for line in result.stdout.strip().split('\n'):
                    line = line.strip()
                    
                    # Check for interface line (starts with "interface:")
                    if line.startswith('interface:'):
                        interface_name = line.split(':', 1)[1].strip()
                        current_interface = {
                            'interface': interface_name,
                            'status': 'connected'
                        }
                        interfaces.append(current_interface)
                    # Check for peer information
                    elif current_interface and line.startswith('endpoint:'):
                        current_interface['endpoint'] = line.split(':', 1)[1].strip()
                    elif current_interface and line.startswith('allowed ips:'):
                        current_interface['allowed_ips'] = line.split(':', 1)[1].strip()
            
            return interfaces
            
        except Exception as e:
            logger.error(f"Error getting active WireGuard interfaces: {e}")
            return []
    
    def _get_available_configs(self) -> List[str]:
        """Get list of available VPN configurations"""
        try:
            configs = []
            for config_file in self.vpn_configs_dir.glob('*.conf'):
                configs.append(config_file.stem)
            return sorted(configs)
        except Exception as e:
            logger.error(f"Error getting available configs: {e}")
            return []
    
    def _get_config_name_for_interface(self, interface_name: str) -> Optional[str]:
        """Get configuration name for a given interface"""
        # This is a simple mapping - in practice, you might want to store this mapping
        # For now, we'll assume the first config is used for wg0
        configs = self._get_available_configs()
        return configs[0] if configs else None
    
    def _get_interface_details(self, interface_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a WireGuard interface"""
        try:
            result = subprocess.run(
                ['sudo', 'wg', 'show', interface_name],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                details = {}
                for line in result.stdout.strip().split('\n'):
                    line = line.strip()
                    if 'endpoint:' in line:
                        details['endpoint'] = line.split(':', 1)[1].strip()
                    elif 'allowed ips:' in line:
                        details['allowed_ips'] = line.split(':', 1)[1].strip()
                    elif 'latest handshake:' in line:
                        details['last_handshake'] = line.split(':', 1)[1].strip()
                    elif 'transfer:' in line:
                        details['transfer'] = line.split(':', 1)[1].strip()
                
                return details
            
        except Exception as e:
            logger.error(f"Error getting interface details: {e}")
        
        return None
    
    def _disconnect_interface(self, interface_name: str) -> VPNResult:
        """Disconnect a specific WireGuard interface"""
        try:
            logger.info(f"Disconnecting VPN interface: {interface_name}")
            
            result = subprocess.run(
                ['sudo', 'wg-quick', 'down', interface_name],
                capture_output=True, text=True, timeout=20
            )
            
            # Clean up system config file
            system_config_path = f"/etc/wireguard/{interface_name}.conf"
            subprocess.run(
                ['sudo', 'rm', '-f', system_config_path],
                capture_output=True, timeout=5
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully disconnected VPN interface: {interface_name}")
                return VPNResult(
                    success=True,
                    message=f"Successfully disconnected from VPN",
                    details=result.stdout.strip()
                )
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                logger.error(f"Failed to disconnect VPN interface {interface_name}: {error_msg}")
                return VPNResult(
                    success=False,
                    message=self._parse_vpn_error(error_msg)
                )
                
        except subprocess.TimeoutExpired:
            logger.error(f"VPN disconnection timed out for interface: {interface_name}")
            return VPNResult(
                success=False,
                message="VPN disconnection timed out. Please try again."
            )
    
    def _disconnect_all_vpn(self) -> VPNResult:
        """Disconnect all active VPN connections"""
        try:
            active_interfaces = self._get_active_wireguard_interfaces()
            
            if not active_interfaces:
                return VPNResult(
                    success=True,
                    message="No active VPN connections to disconnect"
                )
            
            success_count = 0
            errors = []
            
            for interface_info in active_interfaces:
                interface_name = interface_info['interface']
                result = self._disconnect_interface(interface_name)
                
                if result.success:
                    success_count += 1
                else:
                    errors.append(f"{interface_name}: {result.message}")
            
            if success_count == len(active_interfaces):
                return VPNResult(
                    success=True,
                    message=f"Successfully disconnected {success_count} VPN connection(s)"
                )
            elif success_count > 0:
                return VPNResult(
                    success=True,
                    message=f"Disconnected {success_count}/{len(active_interfaces)} connections. Errors: {'; '.join(errors)}"
                )
            else:
                return VPNResult(
                    success=False,
                    message=f"Failed to disconnect VPN connections: {'; '.join(errors)}"
                )
                
        except Exception as e:
            logger.error(f"Error disconnecting all VPN connections: {e}")
            return VPNResult(
                success=False,
                message="Failed to disconnect VPN connections"
            )
    
    def _validate_config_name(self, config_name: str) -> bool:
        """Validate VPN configuration name"""
        if not config_name or len(config_name) > 50:
            return False
        
        # Allow alphanumeric, hyphens, underscores
        pattern = r'^[a-zA-Z0-9\-_]+$'
        return bool(re.match(pattern, config_name))
    
    def _validate_wireguard_config(self, config_content: str) -> bool:
        """Validate WireGuard configuration format"""
        try:
            # Basic validation - check for required sections
            required_sections = ['[Interface]', '[Peer]']
            required_interface_keys = ['PrivateKey']
            required_peer_keys = ['PublicKey', 'Endpoint']
            
            # Check for required sections
            for section in required_sections:
                if section not in config_content:
                    return False
            
            # Check for required keys in Interface section
            interface_section = self._extract_config_section(config_content, '[Interface]')
            for key in required_interface_keys:
                if f"{key} =" not in interface_section:
                    return False
            
            # Check for required keys in Peer section
            peer_section = self._extract_config_section(config_content, '[Peer]')
            for key in required_peer_keys:
                if f"{key} =" not in peer_section:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating WireGuard config: {e}")
            return False
    
    def _extract_config_section(self, config_content: str, section_name: str) -> str:
        """Extract a specific section from WireGuard config"""
        lines = config_content.split('\n')
        in_section = False
        section_lines = []
        
        for line in lines:
            line = line.strip()
            if line == section_name:
                in_section = True
                continue
            elif line.startswith('[') and line.endswith(']'):
                if in_section:
                    break
                in_section = False
                continue
            
            if in_section:
                section_lines.append(line)
        
        return '\n'.join(section_lines)
    
    def _parse_vpn_error(self, error_msg: str) -> str:
        """Parse VPN error message and return user-friendly message"""
        error_lower = error_msg.lower()
        
        if 'permission denied' in error_lower:
            return 'Permission denied. Please check sudo access.'
        elif 'file not found' in error_lower or 'no such file' in error_lower:
            return 'Configuration file not found.'
        elif 'already exists' in error_lower or 'already up' in error_lower:
            return 'VPN connection already active.'
        elif 'timeout' in error_lower:
            return 'Connection timed out. Check your internet connection.'
        elif 'unreachable' in error_lower or 'no route' in error_lower:
            return 'VPN server unreachable. Check endpoint address.'
        elif 'authentication' in error_lower or 'handshake' in error_lower:
            return 'Authentication failed. Check your configuration.'
        else:
            return 'VPN operation failed. Please check your configuration.'