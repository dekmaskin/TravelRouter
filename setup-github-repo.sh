#!/bin/bash

# TravelRouter - GitHub Repository Setup Script
# This script prepares your local repository for GitHub

echo "========================================="
echo "  TravelRouter GitHub Setup"
echo "========================================="
echo ""

# Check if we're in a git repository
if [[ ! -d ".git" ]]; then
    echo "Initializing git repository..."
    git init
    echo "✓ Git repository initialized"
else
    echo "✓ Git repository already exists"
fi

# Add all files
echo ""
echo "Adding files to git..."
git add .

# Create initial commit
echo ""
echo "Creating initial commit..."
git commit -m "Initial commit: TravelRouter v1.0.0

- Professional travel router management system for Raspberry Pi
- WiFi bridge functionality with web interface
- VPN tunnel support with WireGuard
- Security-first design with rate limiting and input validation
- Mobile-optimized responsive interface
- QR code generation and scanning
- Real-time monitoring and system management
- One-command installation and update system"

# Add GitHub remote
echo ""
echo "Adding GitHub remote..."
git branch -M main
git remote add origin https://github.com/dekmaskin/TravelRouter.git

echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Make sure you've created the repository on GitHub:"
echo "   https://github.com/dekmaskin/TravelRouter"
echo ""
echo "2. Push to GitHub:"
echo "   git push -u origin main"
echo ""
echo "3. Your repository will be available at:"
echo "   https://github.com/dekmaskin/TravelRouter"
echo ""
echo "4. The one-command installer will work with:"
echo "   curl -sSL https://raw.githubusercontent.com/dekmaskin/TravelRouter/main/install.sh | sudo bash"
echo ""