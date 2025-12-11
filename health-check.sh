#!/bin/bash

# TravelNet Portal Health Check Script
# Verify all services are running correctly

PI_HOST="10.10.10.60"
PI_USER="johan"

echo "========================================="
echo "  TravelNet Portal Health Check"
echo "========================================="
echo ""

echo "Checking Raspberry Pi connectivity..."
if ping -c 1 $PI_HOST > /dev/null 2>&1; then
    echo "✓ Pi is reachable at $PI_HOST"
else
    echo "✗ Cannot reach Pi at $PI_HOST"
    exit 1
fi

echo ""
echo "Checking services status..."

# Check TravelNet service
echo -n "TravelNet Portal: "
if ssh $PI_USER@$PI_HOST "sudo systemctl is-active travelnet" | grep -q "active"; then
    echo "✓ Running"
else
    echo "✗ Not running"
fi

# Check hostapd
echo -n "Access Point (hostapd): "
if ssh $PI_USER@$PI_HOST "sudo systemctl is-active hostapd" | grep -q "active"; then
    echo "✓ Running"
else
    echo "✗ Not running"
fi

# Check dnsmasq
echo -n "DHCP Server (dnsmasq): "
if ssh $PI_USER@$PI_HOST "sudo systemctl is-active dnsmasq" | grep -q "active"; then
    echo "✓ Running"
else
    echo "✗ Not running"
fi

# Check nginx
echo -n "Web Server (nginx): "
if ssh $PI_USER@$PI_HOST "sudo systemctl is-active nginx" | grep -q "active"; then
    echo "✓ Running"
else
    echo "✗ Not running"
fi

echo ""
echo "Checking network interfaces..."

# Check wlan0 (AP interface)
echo -n "Access Point Interface (wlan0): "
if ssh $PI_USER@$PI_HOST "ip addr show wlan0" | grep -q "192.168.4.1"; then
    echo "✓ Configured with IP 192.168.4.1"
else
    echo "✗ Not properly configured"
fi

# Check wlan1 (WiFi client interface)
echo -n "WiFi Client Interface (wlan1): "
if ssh $PI_USER@$PI_HOST "ip link show wlan1" | grep -q "UP"; then
    echo "✓ Interface is up"
else
    echo "✗ Interface is down"
fi

echo ""
echo "Testing web portal accessibility..."

# Test portal response
echo -n "Portal HTTP Response: "
if ssh $PI_USER@$PI_HOST "curl -s -o /dev/null -w '%{http_code}' http://localhost" | grep -q "200"; then
    echo "✓ Portal responding (HTTP 200)"
else
    echo "✗ Portal not responding properly"
fi

echo ""
echo "Recent log entries:"
echo "==================="
ssh $PI_USER@$PI_HOST "sudo journalctl -u travelnet --no-pager -n 5"

echo ""
echo "Health check complete!"