# System Settings Feature

This document describes the new System Settings page added to the TravelNet Portal travel router application.

## Overview

The System Settings page provides a centralized interface for managing router configuration and system operations. It allows users to:

- Configure hotspot settings (SSID, password, visibility)
- Enable/disable the hotspot while keeping SSH access via ethernet
- Restart network services
- Reboot the system
- View system status and logs

## Features

### Hotspot Configuration
- **SSID Management**: Change the hotspot network name (1-32 characters)
- **Password Management**: Set WPA password (8-63 characters) or leave empty for open network
- **Visibility Control**: Hide/show the hotspot from nearby devices
- **Enable/Disable**: Turn hotspot on/off while maintaining SSH access via ethernet

### Network Management
- **Restart Network**: Restart NetworkManager and related services
- **Refresh Status**: Update network connection information

### System Management
- **System Reboot**: Restart the entire system (if enabled in configuration)
- **View Logs**: Access application, system, and network logs

### System Status
- **Service Status**: Monitor NetworkManager and SSH service status
- **System Uptime**: Display how long the system has been running
- **Memory Usage**: Show current memory utilization

## Access

The System Settings page can be accessed via:
- Navigation menu: "Settings" link in the top navigation bar
- Dashboard: "Settings" button in the quick actions section
- Direct URL: `/system-settings`

## API Endpoints

### Hotspot Management
- `GET /api/v1/hotspot/config` - Get current hotspot configuration
- `POST /api/v1/hotspot/config` - Update hotspot configuration

### System Management
- `GET /api/v1/system/status` - Get comprehensive system status
- `POST /api/v1/system/reboot` - Reboot the system
- `POST /api/v1/system/restart-network` - Restart network services
- `GET /api/v1/system/logs` - Get system logs (application, system, network)

## Security

- All system operations are rate-limited
- System reboot requires explicit configuration flag to be enabled
- Input validation on all configuration changes
- SSH access via ethernet is always maintained regardless of hotspot status

## Files Added/Modified

### New Files
- `templates/system_settings.html` - System settings page template
- `static/js/modules/system-settings.js` - JavaScript functionality
- `static/css/components/system-settings.css` - Styling for system settings
- `SYSTEM_SETTINGS.md` - This documentation

### Modified Files
- `app/web/routes.py` - Added system settings page route
- `app/api/routes.py` - Added system management and hotspot API endpoints
- `app/services/system_service.py` - Added network restart and log viewing functions
- `app/services/network_service.py` - Added hotspot configuration management
- `templates/base.html` - Added navigation link to system settings
- `templates/index.html` - Added settings button to quick actions
- `static/css/main.css` - Imported system settings CSS

## Configuration

The system settings functionality respects the following configuration flags:

- `ENABLE_SYSTEM_REBOOT`: Controls whether system reboot is available
- `ENABLE_QR_GENERATION`: Controls QR code generation features
- `ENABLE_VPN_TUNNEL`: Controls VPN tunnel features

## Usage Examples

### Changing Hotspot SSID and Password
1. Navigate to System Settings
2. Update the "Hotspot SSID" field with desired network name
3. Update the "Hotspot Password" field (or leave empty for open network)
4. Click "Save Hotspot Settings"

### Restarting Network Services
1. Navigate to System Settings
2. Click "Restart Network" in the Network Management section
3. Confirm the action when prompted

### Viewing System Logs
1. Navigate to System Settings
2. Click "View Logs" in the System Management section
3. Select log type (Application, System, or Network) from dropdown
4. Logs will be displayed in the modal window

## Technical Implementation

The system settings functionality is implemented using:

- **Backend**: Flask routes with proper error handling and rate limiting
- **Frontend**: Modern JavaScript with async/await for API calls
- **Styling**: CSS components following the existing design patterns
- **Security**: Input validation and sanitization for all user inputs
- **Logging**: Comprehensive logging of all system operations

## Error Handling

The system includes robust error handling for:
- Network service failures
- Configuration file access issues
- System command execution problems
- Invalid user input
- Rate limiting violations

All errors are logged and user-friendly messages are displayed to the user.