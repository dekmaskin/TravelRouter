"""
System Service Module

Business logic for system operations including reboot, SSH management,
and system status monitoring.
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
    
    def manage_ssh(self, action: str) -> SystemActionResult:
        """
        Manage SSH service
        
        Args:
            action: 'enable', 'disable', or 'status'
            
        Returns:
            SystemActionResult object
            
        Raises:
            SecurityError: If SSH management is not enabled
        """
        if not current_app.config['ENABLE_SSH_MANAGEMENT']:
            security_logger.warning(f"SSH {action} attempt when feature is disabled")
            raise SecurityError("SSH management is not enabled")
        
        try:
            if action == 'enable':
                return self._enable_ssh()
            elif action == 'disable':
                return self._disable_ssh()
            elif action == 'status':
                return self._get_ssh_status()
            else:
                raise ValueError(f"Invalid SSH action: {action}")
                
        except Exception as e:
            logger.error(f"Error managing SSH ({action}): {e}")
            return SystemActionResult(
                success=False,
                message=f'SSH {action} operation failed'
            )
    
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
            
            # Check SSH status if enabled
            if current_app.config['ENABLE_SSH_MANAGEMENT']:
                ssh_result = self._get_ssh_status()
                status['services']['ssh'] = {
                    'enabled': ssh_result.success and 'active' in ssh_result.message.lower(),
                    'status': ssh_result.message
                }
            
            # Add system information
            status['system'] = {
                'reboot_enabled': current_app.config['ENABLE_SYSTEM_REBOOT'],
                'ssh_management_enabled': current_app.config['ENABLE_SSH_MANAGEMENT'],
                'qr_generation_enabled': current_app.config['ENABLE_QR_GENERATION']
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'success': False,
                'error': 'Failed to retrieve system status'
            }
    
    def _enable_ssh(self) -> SystemActionResult:
        """Enable SSH service"""
        security_logger.warning("SSH service enable requested")
        
        try:
            # Enable SSH service
            subprocess.run(
                self.allowed_commands['enable_ssh'],
                capture_output=True, timeout=10
            )
            
            # Start SSH service
            subprocess.run(
                self.allowed_commands['start_ssh'],
                capture_output=True, timeout=10
            )
            
            return SystemActionResult(
                success=True,
                message='SSH service enabled and started'
            )
            
        except subprocess.TimeoutExpired:
            return SystemActionResult(
                success=False,
                message='SSH enable operation timed out'
            )
        except Exception as e:
            logger.error(f"Error enabling SSH: {e}")
            return SystemActionResult(
                success=False,
                message='Failed to enable SSH service'
            )
    
    def _disable_ssh(self) -> SystemActionResult:
        """Disable SSH service"""
        security_logger.warning("SSH service disable requested")
        
        try:
            # Stop SSH service
            subprocess.run(
                self.allowed_commands['stop_ssh'],
                capture_output=True, timeout=10
            )
            
            return SystemActionResult(
                success=True,
                message='SSH service stopped'
            )
            
        except subprocess.TimeoutExpired:
            return SystemActionResult(
                success=False,
                message='SSH disable operation timed out'
            )
        except Exception as e:
            logger.error(f"Error disabling SSH: {e}")
            return SystemActionResult(
                success=False,
                message='Failed to disable SSH service'
            )
    
    def _get_ssh_status(self) -> SystemActionResult:
        """Get SSH service status"""
        try:
            result = subprocess.run(
                self.allowed_commands['ssh_status'],
                capture_output=True, text=True, timeout=10
            )
            
            is_active = result.stdout.strip() == 'active'
            
            return SystemActionResult(
                success=True,
                message='active' if is_active else 'inactive',
                details=f'SSH service is {"running" if is_active else "stopped"}'
            )
            
        except subprocess.TimeoutExpired:
            return SystemActionResult(
                success=False,
                message='SSH status check timed out'
            )
        except Exception as e:
            logger.error(f"Error checking SSH status: {e}")
            return SystemActionResult(
                success=False,
                message='Failed to check SSH status'
            )