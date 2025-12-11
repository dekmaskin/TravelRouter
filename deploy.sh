#!/bin/bash

# TravelNet Portal Deployment Script
# Deploy from development machine to Raspberry Pi

set -e

# Configuration - Update these for your setup
PI_HOST="${PI_HOST:-pi@raspberrypi.local}"
REMOTE_DIR="${REMOTE_DIR:-/home/pi/travelnet-portal}"
LOCAL_DIR="."

echo "========================================="
echo "  TravelNet Portal Deployment"
echo "========================================="
echo ""

# Check if environment variables are set
if [[ "$PI_HOST" == "pi@raspberrypi.local" ]]; then
    echo "Please set PI_HOST environment variable or update this script"
    echo "Example: export PI_HOST=pi@192.168.1.100"
    echo "Or edit the PI_HOST variable in this script"
    exit 1
fi

# Extract hostname for ping test
PI_IP=$(echo $PI_HOST | cut -d'@' -f2)

# Check if we can reach the Pi
echo "Checking connection to Raspberry Pi at $PI_IP..."
if ! ping -c 1 $PI_IP > /dev/null 2>&1; then
    echo "Error: Cannot reach Raspberry Pi at $PI_IP"
    echo "Please check:"
    echo "- Pi is powered on and connected to network"
    echo "- IP address/hostname is correct"
    echo "- Network connectivity"
    exit 1
fi

echo "✓ Pi is reachable"

# Test SSH connection
echo "Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes $PI_HOST exit 2>/dev/null; then
    echo "Error: Cannot SSH to Pi. Please ensure:"
    echo "- SSH is enabled on the Pi"
    echo "- SSH keys are set up or password authentication is enabled"
    echo "- User exists on the Pi"
    exit 1
fi

echo "✓ SSH connection successful"

# Create remote directory
echo "Creating remote directory..."
ssh $PI_HOST "mkdir -p $REMOTE_DIR"

# Copy files to Pi
echo "Copying files to Raspberry Pi..."
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.vscode' \
    --exclude='logs/' \
    --exclude='venv/' \
    --exclude='.env.production' \
    $LOCAL_DIR/ $PI_HOST:$REMOTE_DIR/

echo "✓ Files copied successfully"

# Make scripts executable
echo "Setting up permissions..."
ssh $PI_HOST "chmod +x $REMOTE_DIR/setup-secure.sh $REMOTE_DIR/setup.sh $REMOTE_DIR/health-check.sh"

echo "✓ Permissions set"

echo ""
echo "========================================="
echo "  Deployment Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. SSH into your Pi: ssh $PI_HOST"
echo "2. Navigate to project: cd $REMOTE_DIR"
echo "3. Run setup script: sudo ./setup-secure.sh"
echo ""
echo "Or run the setup remotely:"
echo "ssh -t $PI_HOST 'cd $REMOTE_DIR && sudo ./setup-secure.sh'"
echo ""

read -p "Would you like to run the setup script now? (y/N): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running setup script on Pi..."
    ssh -t $PI_HOST "cd $REMOTE_DIR && sudo ./setup-secure.sh"
fi

echo "Deployment finished!"
echo ""
echo "To check system health after setup:"
echo "ssh $PI_HOST 'cd $REMOTE_DIR && sudo ./health-check.sh'"
echo ""