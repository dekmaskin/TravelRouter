"""
System Service Module

Business logic for system operations including reboot and system status monitoring.
"""

import subprocess
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from flask import current_app

from app.core.errors import SecurityError, NetworkError

logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')


@dataclass
class SystemActionResult:
    """Data class for system action results"""
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


class SystemService:
    """Service class for system operations"""
    
    def __init__(self):
        self.allowed_commands = current_app.config['ALLOWED_SYSTEM_COMMANDS']
    
    def reboot_system(self) -> SystemActionResult:
        """
        Reboot the system
        
        Returns:
            SystemActionResult object
            
        Raises:
            SecurityError: If reboot is not enabled
        """
        if not current_app.config['ENABLE_SYSTEM_REBOOT']:
            security_logger.warning("Reboot attempt when feature is disabled")
            raise SecurityError("System reboot is not enabled")
        
        try:
            security_logger.warning("System reboot initiated")
            
            # Use the whitelisted reboot command
            cmd = self.allowed_commands['reboot']
            subprocess.run(cmd, timeout=5)
            
            return SystemActionResult(
                success=True,
                message='System reboot initiated. The system will restart shortly.'
            )
            
        except subprocess.TimeoutExpired:
            # This is expected for reboot command
            return SystemActionResult(
                success=True,
                message='System reboot initiated'
            )
        except Exception as e:
            logger.error(f"Error rebooting system: {e}")
            return SystemActionResult(
                success=False,
                message='Failed to initiate system reboot'
            )
    

    
    def restart_network(self) -> SystemActionResult:
        """
        Restart network services
        
        Returns:
            SystemActionResult object
        """
        try:
            security_logger.info("Network restart initiated")
            
            # Restart NetworkManager service
            cmd = ['sudo', 'systemctl', 'restart', 'NetworkManager']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("Network services restarted successfully")
                return SystemActionResult(
                    success=True,
                    message='Network services restarted successfully'
                )
            else:
                logger.error(f"Failed to restart network: {result.stderr}")
                return SystemActionResult(
                    success=False,
                    message='Failed to restart network services'
                )
                
        except subprocess.TimeoutExpired:
            logger.error("Network restart timed out")
            return SystemActionResult(
                success=False,
                message='Network restart timed out'
            )
        except Exception as e:
            logger.error(f"Error restarting network: {e}")
            return SystemActionResult(
                success=False,
                message='Failed to restart network services'
            )
    
    def update_system(self) -> SystemActionResult:
        """
        Update the system using the update script (without health check)
        
        Returns:
            SystemActionResult object
            
        Raises:
            SecurityError: If system update is not enabled
        """
        if not current_app.config['ENABLE_SYSTEM_UPDATE']:
            security_logger.warning("System update attempt when feature is disabled")
            raise SecurityError("System update is not enabled")
        
        try:
            security_logger.warning("System update initiated")
            
            # Path to the update script
            update_script = '/opt/travelnet/update.sh'
            
            # Check if update script exists
            import os
            if not os.path.exists(update_script):
                logger.error(f"Update script not found at {update_script}")
                return SystemActionResult(
                    success=False,
                    message='Update script not found'
                )
            
            # Create update status file
            status_file = '/tmp/travelnet_update_status'
            with open(status_file, 'w') as f:
                f.write('STARTING\n')
            
            # Run the update script in the background with status tracking
            # Use nohup to ensure the script survives service shutdown
            cmd = ['nohup', 'sudo', 'bash', update_script]
            
            # Start the process but don't wait for completion
            # Use a separate session to prevent it from being killed with the service
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                start_new_session=True
            )
            
            logger.info(f"Update process started with PID: {process.pid}")
            
            return SystemActionResult(
                success=True,
                message='System update initiated. The update will run in the background and may restart services.',
                details=f'Update process started with PID: {process.pid}'
            )
            
        except Exception as e:
            logger.error(f"Error starting system update: {e}")
            return SystemActionResult(
                success=False,
                message='Failed to start system update'
            )
    
    def get_update_status(self) -> Dict[str, Any]:
        """
        Get current update status
        
        Returns:
            Dictionary with update status information
        """
        try:
            import os
            status_file = '/tmp/travelnet_update_status'
            
            # Check if update is running by looking for update processes
            result = subprocess.run(
                ['pgrep', '-f', 'update.sh'],
                capture_output=True, text=True, timeout=5
            )
            
            is_running = result.returncode == 0
            
            # Try to read status file
            status_message = 'No update in progress'
            if os.path.exists(status_file):
                try:
                    with open(status_file, 'r') as f:
                        status_message = f.read().strip()
                except:
                    pass
            
            return {
                'success': True,
                'update_running': is_running,
                'status': status_message,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting update status: {e}")
            return {
                'success': False,
                'error': 'Failed to get update status',
                'update_running': False
            }
    
    def _check_internet_connectivity(self) -> bool:
        """
        Check if internet connectivity is available
        
        Returns:
            bool: True if internet is available, False otherwise
        """
        try:
            # Try to ping a reliable DNS server (Google's 8.8.8.8)
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '3', '8.8.8.8'],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                return True
            
            # If ping fails, try a different approach - DNS lookup
            result = subprocess.run(
                ['nslookup', 'google.com'],
                capture_output=True, text=True, timeout=5
            )
            
            return result.returncode == 0
            
        except (subprocess.TimeoutExpired, Exception) as e:
            logger.warning(f"Internet connectivity check failed: {e}")
            return False
    
    def get_system_logs(self, log_type: str = 'application', lines: int = 100) -> Dict[str, Any]:
        """
        Get system logs
        
        Args:
            log_type: Type of logs to retrieve ('application', 'system', 'network')
            lines: Number of lines to retrieve
            
        Returns:
            Dictionary with log content
        """
        try:
            if log_type == 'application':
                # Get application logs
                log_file = current_app.config['LOG_FILE']
                if log_file.exists():
                    cmd = ['tail', '-n', str(lines), str(log_file)]
                else:
                    return {
                        'success': True,
                        'logs': 'No application logs found',
                        'log_type': log_type
                    }
            elif log_type == 'system':
                # Get system logs from journalctl
                cmd = ['sudo', 'journalctl', '-n', str(lines), '--no-pager']
            elif log_type == 'network':
                # Get NetworkManager logs
                cmd = ['sudo', 'journalctl', '-u', 'NetworkManager', '-n', str(lines), '--no-pager']
            else:
                return {
                    'success': False,
                    'error': 'Invalid log type'
                }
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'logs': result.stdout,
                    'log_type': log_type
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to retrieve {log_type} logs'
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Log retrieval timed out'
            }
        except Exception as e:
            logger.error(f"Error getting system logs: {e}")
            return {
                'success': False,
                'error': 'Failed to retrieve logs'
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status
        
        Returns:
            Dictionary with system status information
        """
        try:
            status = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'services': {},
                'system': {}
            }
            
            # Check NetworkManager status
            try:
                result = subprocess.run(
                    ['sudo', 'systemctl', 'is-active', 'NetworkManager'],
                    capture_output=True, text=True, timeout=5
                )
                status['services']['network_manager'] = {
                    'active': result.returncode == 0,
                    'status': result.stdout.strip()
                }
            except Exception as e:
                logger.warning(f"Could not check NetworkManager status: {e}")
                status['services']['network_manager'] = {
                    'active': False,
                    'status': 'unknown'
                }
            
            # Check SSH status
            try:
                result = subprocess.run(
                    ['sudo', 'systemctl', 'is-active', 'ssh'],
                    capture_output=True, text=True, timeout=5
                )
                status['services']['ssh'] = {
                    'active': result.returncode == 0,
                    'status': result.stdout.strip()
                }
            except Exception as e:
                logger.warning(f"Could not check SSH status: {e}")
                status['services']['ssh'] = {
                    'active': False,
                    'status': 'unknown'
                }
            
            # Get system uptime
            try:
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.read().split()[0])
                    uptime_hours = int(uptime_seconds // 3600)
                    uptime_minutes = int((uptime_seconds % 3600) // 60)
                    status['system']['uptime'] = f"{uptime_hours}h {uptime_minutes}m"
            except Exception as e:
                logger.warning(f"Could not get uptime: {e}")
                status['system']['uptime'] = 'unknown'
            
            # Get memory usage
            try:
                result = subprocess.run(
                    ['free', '-m'], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) >= 2:
                        mem_line = lines[1].split()
                        if len(mem_line) >= 3:
                            total_mem = int(mem_line[1])
                            used_mem = int(mem_line[2])
                            mem_percent = round((used_mem / total_mem) * 100, 1)
                            status['system']['memory'] = {
                                'total_mb': total_mem,
                                'used_mb': used_mem,
                                'usage_percent': mem_percent
                            }
            except Exception as e:
                logger.warning(f"Could not get memory usage: {e}")
                status['system']['memory'] = {'usage_percent': 0}
            
            # Check internet connectivity
            internet_connected = self._check_internet_connectivity()
            
            # Add system information
            status['system'].update({
                'reboot_enabled': current_app.config['ENABLE_SYSTEM_REBOOT'],
                'update_enabled': current_app.config['ENABLE_SYSTEM_UPDATE'],
                'qr_generation_enabled': current_app.config['ENABLE_QR_GENERATION'],
                'vpn_tunnel_enabled': current_app.config['ENABLE_VPN_TUNNEL'],
                'internet_connected': internet_connected
            })
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'success': False,
                'error': 'Failed to retrieve system status'
            }
    
