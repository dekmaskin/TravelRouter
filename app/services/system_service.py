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
            

            
            # Add system information
            status['system'] = {
                'reboot_enabled': current_app.config['ENABLE_SYSTEM_REBOOT'],
                'qr_generation_enabled': current_app.config['ENABLE_QR_GENERATION']
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'success': False,
                'error': 'Failed to retrieve system status'
            }
    
