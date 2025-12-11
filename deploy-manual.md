# Manual Deployment Guide for TravelNet Portal

Since SSH key authentication isn't set up, here's how to deploy manually:

## Step 1: Copy Files to Raspberry Pi

### Option A: Using SCP (will prompt for password)
```bash
scp -r . johan@10.10.10.60:/home/johan/travelnet-portal/
```

### Option B: Using SFTP
```bash
sftp johan@10.10.10.60
mkdir travelnet-portal
put -r * travelnet-portal/
quit
```

### Option C: Using rsync (will prompt for password)
```bash
rsync -avz --progress --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.vscode' --exclude='logs/' --exclude='venv/' . johan@10.10.10.60:/home/johan/travelnet-portal/
```

## Step 2: SSH into Raspberry Pi
```bash
ssh johan@10.10.10.60
```

## Step 3: Navigate to Project Directory
```bash
cd /home/johan/travelnet-portal
```

## Step 4: Make Scripts Executable
```bash
chmod +x setup.sh deploy.sh deploy-production.sh health-check.sh
```

## Step 5: Run Setup Script
```bash
sudo ./setup.sh
```

## Step 6: Verify Deployment
```bash
sudo systemctl status travelnet
sudo systemctl status hostapd
sudo systemctl status dnsmasq
```

## Step 7: Test the Portal
1. Connect to WiFi network: `TravelNet-<hostname>`
2. Password: `TravelNet123`
3. Open browser: `http://192.168.4.1`

## Troubleshooting Commands
```bash
# Check service logs
sudo journalctl -u travelnet -f

# Restart services
sudo systemctl restart travelnet
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq

# Check network interfaces
ip addr show
nmcli device status

# Test portal locally
curl http://localhost
```