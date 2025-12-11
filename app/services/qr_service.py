"""
QR Code Service Module

Business logic for QR code generation with security validation
and proper error handling.
"""

import qrcode
import io
import base64
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from flask import current_app

from app.core.errors import ValidationError, SecurityError
from app.core.security import security_manager

logger = logging.getLogger(__name__)


@dataclass
class QRCodeResult:
    """Data class for QR code generation results"""
    success: bool
    qr_code: Optional[str] = None
    ssid: Optional[str] = None
    security: Optional[str] = None
    message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {'success': self.success}
        
        if self.success:
            result.update({
                'qr_code': self.qr_code,
                'ssid': self.ssid,
                'security': self.security
            })
        else:
            result['message'] = self.message
            
        return result


class QRCodeService:
    """Service class for QR code operations"""
    
    def __init__(self):
        self.allowed_security_types = ['OPEN', 'WPA', 'WPA2', 'WEP']
    
    def generate_wifi_qr(self, ssid: str, password: str = '', security: str = 'WPA') -> QRCodeResult:
        """
        Generate QR code for WiFi connection
        
        Args:
            ssid: Network SSID
            password: Network password (optional for open networks)
            security: Security type (OPEN, WPA, WPA2, WEP)
            
        Returns:
            QRCodeResult object
            
        Raises:
            SecurityError: If QR generation is disabled
            ValidationError: If input validation fails
        """
        try:
            # Check if QR generation is enabled
            if not current_app.config['ENABLE_QR_GENERATION']:
                raise SecurityError("QR code generation is disabled")
            
            # Validate and sanitize inputs
            sanitized_ssid = security_manager.sanitize_ssid(ssid)
            if not sanitized_ssid:
                raise ValidationError('Invalid SSID format', 'ssid')
            
            # Validate security type
            security_upper = security.upper()
            if security_upper not in self.allowed_security_types:
                security_upper = 'WPA'  # Default to WPA
            
            # Validate password if provided
            if password and not security_manager._validate_password(password):
                raise ValidationError('Invalid password format or length', 'password')
            
            logger.info(f"QR code generation requested for SSID: {sanitized_ssid[:10]}...")
            
            # Create WiFi QR code string
            wifi_string = self._create_wifi_string(sanitized_ssid, password, security_upper)
            
            # Generate QR code image
            qr_code_data = self._generate_qr_image(wifi_string)
            
            logger.info(f"QR code generated successfully for {sanitized_ssid[:10]}...")
            
            return QRCodeResult(
                success=True,
                qr_code=qr_code_data,
                ssid=sanitized_ssid,
                security=security_upper
            )
            
        except (SecurityError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return QRCodeResult(
                success=False,
                message='QR code generation failed'
            )
    
    def _create_wifi_string(self, ssid: str, password: str, security: str) -> str:
        """
        Create WiFi QR code string with proper escaping
        
        Args:
            ssid: Sanitized SSID
            password: Network password
            security: Security type
            
        Returns:
            WiFi QR code string
        """
        if security == 'OPEN' or not password:
            return f"WIFI:T:nopass;S:{ssid};;"
        else:
            # Escape special characters in password for QR code
            escaped_password = self._escape_qr_string(password)
            escaped_ssid = self._escape_qr_string(ssid)
            return f"WIFI:T:{security};S:{escaped_ssid};P:{escaped_password};;"
    
    def _escape_qr_string(self, text: str) -> str:
        """
        Escape special characters for QR code WiFi strings
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text
        """
        # Escape special characters according to QR WiFi specification
        return (text.replace('\\', '\\\\')
                   .replace(';', '\\;')
                   .replace(',', '\\,')
                   .replace('"', '\\"')
                   .replace(':', '\\:'))
    
    def _generate_qr_image(self, data: str) -> str:
        """
        Generate QR code image and return as base64 data URL
        
        Args:
            data: Data to encode in QR code
            
        Returns:
            Base64 encoded data URL
        """
        # Create QR code with error correction
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4
        )
        
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for web display
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        return f'data:image/png;base64,{img_base64}'
    
    @staticmethod
    def parse_wifi_qr(qr_data: str) -> Optional[Dict[str, str]]:
        """
        Parse WiFi QR code data string
        
        Args:
            qr_data: QR code data string
            
        Returns:
            Dictionary with WiFi network information or None if invalid
        """
        try:
            # WiFi QR code format: WIFI:T:WPA;S:MyNetwork;P:MyPassword;;
            import re
            
            # Match WiFi QR code pattern
            pattern = r'^WIFI:T:([^;]*);S:([^;]*);P:([^;]*);'
            match = re.match(pattern, qr_data)
            
            if match:
                security = match.group(1) or 'Open'
                ssid = match.group(2)
                password = match.group(3)
                
                # Unescape special characters
                ssid = ssid.replace('\\;', ';').replace('\\,', ',').replace('\\:', ':').replace('\\"', '"').replace('\\\\', '\\')
                password = password.replace('\\;', ';').replace('\\,', ',').replace('\\:', ':').replace('\\"', '"').replace('\\\\', '\\')
                
                return {
                    'ssid': ssid,
                    'password': password if security != 'nopass' else '',
                    'security': security
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing WiFi QR code: {e}")
            return None