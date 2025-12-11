#!/bin/bash

# TravelNet Portal Deployment Script
# Deploy from Windows development machine to Raspberry Pi

set -e

# Configuration
PI_HOST="10.10.10.60"
PI_USER="johan"
REMOTE_DIR="/home/johan/travelnet-portal"
LOCAL_DIR="."

echo "========================================="
echo "  TravelNet Portal Deployment"
echo "========================================="
echo ""

# Check if we can reach the Pi
echo "Checking connection to Raspberry Pi..."
if ! ping -c 1 $PI_HOST > /dev/null 2>&1; then
    echo "Error: Cannot reach Raspberry Pi at $PI_HOST"
    echo "Please check:"
    echo "- Pi is powered on and connected to network"
    echo "- IP address is correct"
    echo "- SSH is enabled on the Pi"
    exit 1
fi

echo "✓ Pi is reachable"

# Test SSH connection
echo "Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes $PI_USER@$PI_HOST exit 2>/dev/null; then
    echo "Error: Cannot SSH to Pi. Please ensure:"
    echo "- SSH is enabled on the Pi"
    echo "- SSH keys are set up or password authentication is enabled"
    echo "- User '$PI_USER' exists on the Pi"
    exit 1
fi

echo "✓ SSH connection successful"

# Create remote directory
echo "Creating remote directory..."
ssh $PI_USER@$PI_HOST "mkdir -p $REMOTE_DIR"

# Copy files to Pi
echo "Copying files to Raspberry Pi..."
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.vscode' \
    --exclude='logs/' \
    --exclude='venv/' \
    $LOCAL_DIR/ $PI_USER@$PI_HOST:$REMOTE_DIR/

echo "✓ Files copied successfully"

# Make scripts executable
echo "Setting up permissions..."
ssh $PI_USER@$PI_HOST "chmod +x $REMOTE_DIR/setup.sh $REMOTE_DIR/deploy.sh"

echo "✓ Permissions set"

echo ""
echo "========================================="
echo "  Deployment Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. SSH into your Pi: ssh $PI_USER@$PI_HOST"
echo "2. Navigate to project: cd $REMOTE_DIR"
echo "3. Run setup script: sudo ./setup.sh"
echo ""
echo "Or run the setup remotely:"
echo "ssh $PI_USER@$PI_HOST 'cd $REMOTE_DIR && sudo ./setup.sh'"
echo ""

read -p "Would you like to run the setup script now? (y/N): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running setup script on Pi..."
    ssh -t $PI_USER@$PI_HOST "cd $REMOTE_DIR && sudo ./setup.sh"
fi

echo "Deployment finished!"