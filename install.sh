#!/bin/bash

# TravelNet Portal - One-Click Installation Script
# Downloads and runs the secure setup for TravelNet Portal

set -e

# Configuration - Update these for your repository
REPO_URL="https://github.com/dekmaskin/TravelRouter"
TEMP_DIR="/tmp/travelnet-install"
SCRIPT_NAME="setup-secure.sh"

echo "========================================="
echo "  TravelNet Portal Installer"
echo "========================================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 
   exit 1
fi

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    apt update && apt install -y git
fi

echo "Downloading TravelNet Portal from $REPO_URL..."
rm -rf $TEMP_DIR

if ! git clone $REPO_URL $TEMP_DIR; then
    echo "Error: Failed to clone repository"
    echo "Please update REPO_URL in this script with your GitHub repository URL"
    exit 1
fi

echo "Starting installation..."
cd $TEMP_DIR
chmod +x $SCRIPT_NAME

if [[ -f $SCRIPT_NAME ]]; then
    ./$SCRIPT_NAME
else
    echo "Error: $SCRIPT_NAME not found in repository"
    exit 1
fi

echo "Cleaning up temporary files..."
rm -rf $TEMP_DIR

echo ""
echo "========================================="
echo "Installation Complete!"
echo "========================================="
echo ""
echo "Your TravelNet Portal is now ready to use."
echo "Connect to the WiFi network and open your browser to get started."
echo ""