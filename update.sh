#!/bin/bash

# TravelNet Portal Update Script
# Updates an existing TravelNet Portal installation

# Function to ensure service is restarted even if update fails
cleanup_and_restart() {
    echo ""
    echo "Ensuring service is restarted..."
    systemctl daemon-reload
    systemctl start $SERVICE_NAME || echo "Warning: Failed to start service"
    
    # Clean up status file
    rm -f "$STATUS_FILE" 2>/dev/null || true
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "✓ $SERVICE_NAME service is running"
    else
        echo "✗ Warning: $SERVICE_NAME service may not be running properly"
        echo "  Check logs: journalctl -u $SERVICE_NAME -f"
    fi
}

# Set trap to ensure cleanup happens even if script fails
trap cleanup_and_restart EXIT

set -e

# Configuration
APP_DIR="/opt/travelnet"
SERVICE_NAME="travelnet"
BACKUP_DIR="$APP_DIR/backups/update-$(date +%Y%m%d-%H%M%S)"
REPO_URL="${REPO_URL:-https://github.com/dekmaskin/TravelRouter}"
TEMP_DIR="/tmp/travelnet-update"
STATUS_FILE="/tmp/travelnet_update_status"

# Function to update status
update_status() {
    echo "$1" > "$STATUS_FILE"
    echo "$1"
}

# Load environment variables if available
if [[ -f $APP_DIR/.env.production ]]; then
    set -a
    source $APP_DIR/.env.production 2>/dev/null || true
    set +a
fi

APP_NAME="${APP_NAME:-TravelNet Portal}"

echo "========================================="
echo "  $APP_NAME Update Script"
echo "========================================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 
   exit 1
fi

# Check if TravelNet is installed
if [[ ! -d "$APP_DIR" ]]; then
    echo "Error: TravelNet Portal is not installed in $APP_DIR"
    echo "Please run the installation script first."
    exit 1
fi

# Check if service exists
if ! systemctl list-unit-files | grep -q "$SERVICE_NAME.service"; then
    echo "Error: $SERVICE_NAME service not found"
    echo "Please run the installation script first."
    exit 1
fi

echo "Current installation found at: $APP_DIR"
echo "Service: $SERVICE_NAME"
echo ""

# Create backup
update_status "Creating backup..."
mkdir -p "$BACKUP_DIR"

# Backup current application
echo "  - Backing up application files..."
cp -r "$APP_DIR/app" "$BACKUP_DIR/" 2>/dev/null || true
cp -r "$APP_DIR/static" "$BACKUP_DIR/" 2>/dev/null || true
cp -r "$APP_DIR/templates" "$BACKUP_DIR/" 2>/dev/null || true
cp "$APP_DIR/config.py" "$BACKUP_DIR/" 2>/dev/null || true
cp "$APP_DIR/run.py" "$BACKUP_DIR/" 2>/dev/null || true
cp "$APP_DIR/requirements.txt" "$BACKUP_DIR/" 2>/dev/null || true

# Backup configuration
echo "  - Backing up configuration..."
cp "$APP_DIR/.env.production" "$BACKUP_DIR/" 2>/dev/null || true
cp "/etc/systemd/system/$SERVICE_NAME.service" "$BACKUP_DIR/" 2>/dev/null || true

echo "✓ Backup created at: $BACKUP_DIR"

# Stop services
echo ""
update_status "Stopping services..."
systemctl stop $SERVICE_NAME || echo "  Warning: Could not stop $SERVICE_NAME service"
echo "✓ Services stopped"

# Download latest version
echo ""
update_status "Downloading latest version..."
rm -rf $TEMP_DIR

if [[ "$REPO_URL" == *"YOUR_USERNAME"* ]]; then
    echo "Error: Please update REPO_URL in this script with your GitHub repository URL"
    echo "Or set it as an environment variable: export REPO_URL=https://github.com/username/repo"
    exit 1
fi

if ! git clone $REPO_URL $TEMP_DIR 2>&1; then
    echo "Error: Failed to download latest version from $REPO_URL"
    echo "Please check the repository URL and your internet connection"
    echo "Attempting to restart service anyway..."
    exit 1
fi

echo "✓ Latest version downloaded"

# Update application files
echo ""
update_status "Updating application files..."

# Update Python application
echo "  - Updating Python application..."
cp -r $TEMP_DIR/app/* $APP_DIR/app/ 2>/dev/null || true
cp $TEMP_DIR/config.py $APP_DIR/ 2>/dev/null || true
cp $TEMP_DIR/run.py $APP_DIR/ 2>/dev/null || true

# Update static files
echo "  - Updating static files..."
cp -r $TEMP_DIR/static/* $APP_DIR/static/ 2>/dev/null || true

# Update templates
echo "  - Updating templates..."
cp -r $TEMP_DIR/templates/* $APP_DIR/templates/ 2>/dev/null || true

# Update requirements
echo "  - Updating requirements..."
cp $TEMP_DIR/requirements.txt $APP_DIR/ 2>/dev/null || true

# Update version file
echo "  - Updating version information..."
cp $TEMP_DIR/VERSION $APP_DIR/ 2>/dev/null || true

# Update scripts
echo "  - Updating management scripts..."
cp $TEMP_DIR/health-check.sh $APP_DIR/ 2>/dev/null || true
chmod +x $APP_DIR/health-check.sh 2>/dev/null || true

# Handle update script self-update carefully
if [[ -f "$TEMP_DIR/update.sh" ]]; then
    # Check if the new update script is different
    if ! cmp -s "$TEMP_DIR/update.sh" "$APP_DIR/update.sh" 2>/dev/null; then
        echo "  - New update script detected, will update after completion..."
        # Copy to a temporary location for post-update replacement
        cp "$TEMP_DIR/update.sh" "$APP_DIR/update.sh.new" 2>/dev/null || true
        chmod +x "$APP_DIR/update.sh.new" 2>/dev/null || true
    fi
fi

echo "✓ Application files updated"

# Update system packages
echo ""
update_status "Updating system packages..."
echo "  - Updating package lists..."
apt-get update

echo "  - Upgrading system packages..."
update_status "Installing system package updates..."
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

echo "  - Cleaning up package cache..."
apt-get autoremove -y
apt-get autoclean

echo "✓ System packages updated"

# Update Python dependencies
echo ""
update_status "Updating Python dependencies..."
cd $APP_DIR

if [[ -d "venv" ]]; then
    echo "  - Activating virtual environment..."
    source venv/bin/activate
    echo "  - Installing/updating dependencies..."
    pip install -r requirements.txt --upgrade
    deactivate
else
    echo "  - Installing dependencies system-wide..."
    pip3 install -r requirements.txt --upgrade
fi

echo "✓ Dependencies updated"

# Set permissions
echo ""
update_status "Setting permissions..."
chown -R johan:johan $APP_DIR 2>/dev/null || chown -R pi:pi $APP_DIR 2>/dev/null || true
chmod +x $APP_DIR/*.sh 2>/dev/null || true
echo "✓ Permissions set"

# Start services
echo ""
update_status "Starting services..."
# Service restart is handled by the cleanup trap

# Cleanup
echo ""
update_status "Cleaning up..."
rm -rf $TEMP_DIR
echo "✓ Temporary files cleaned up"

# Mark update as complete
update_status "Update completed successfully"

# Disable the trap since we're completing successfully
trap - EXIT

echo ""
echo "========================================="
echo "  Update Complete!"
echo "========================================="
echo ""
echo "Update Summary:"
echo "- Backup created: $BACKUP_DIR"
echo "- System packages updated"
echo "- Application files updated"
echo "- Dependencies updated"
echo "- Services restarted"
echo ""
echo "Next Steps:"
echo "1. Test the portal: http://192.168.4.1"
echo "2. Check service status: systemctl status $SERVICE_NAME"
echo "3. View logs: journalctl -u $SERVICE_NAME -f"
echo "4. Run health check manually if needed: $APP_DIR/health-check.sh"
echo ""



echo ""
echo "If you encounter any issues, you can restore from backup:"
echo "  sudo systemctl stop $SERVICE_NAME"
echo "  sudo cp -r $BACKUP_DIR/* $APP_DIR/"
echo "  sudo systemctl start $SERVICE_NAME"
echo ""
echo "Update completed successfully!"

# Handle update script self-replacement if needed
if [[ -f "$APP_DIR/update.sh.new" ]]; then
    echo ""
    echo "Updating update script for next time..."
    mv "$APP_DIR/update.sh.new" "$APP_DIR/update.sh" 2>/dev/null || true
    chmod +x "$APP_DIR/update.sh" 2>/dev/null || true
    echo "✓ Update script updated for future updates"
fi

# Final cleanup and service restart
cleanup_and_restart