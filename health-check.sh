#!/bin/bash

# TravelNet Portal Health Check Script
# Verify all services are running correctly

set -e

# Load environment variables if available
if [[ -f /opt/travelnet/.env.production ]]; then
    set -a  # automatically export all variables
    source /opt/travelnet/.env.production 2>/dev/null || true
    set +a  # stop automatically exporting
fi

# Default values if not set in environment
APP_NAME="${APP_NAME:-TravelNet Portal}"
AP_INTERFACE="${AP_INTERFACE:-wlan0}"
WIFI_INTERFACE="${WIFI_INTERFACE:-wlan1}"

echo "========================================="
echo "  $APP_NAME Health Check"
echo "========================================="
echo ""

echo "Checking system services..."

# Check TravelNet service
echo -n "TravelNet Portal Service: "
if systemctl is-active --quiet travelnet 2>/dev/null; then
    echo "✓ Running"
else
    echo "✗ Not running"
fi

# Check hostapd
echo -n "Access Point (hostapd): "
if systemctl is-active --quiet hostapd 2>/dev/null; then
    echo "✓ Running"
else
    echo "✗ Not running"
fi

# Check dnsmasq
echo -n "DHCP Server (dnsmasq): "
if systemctl is-active --quiet dnsmasq 2>/dev/null; then
    echo "✓ Running"
else
    echo "✗ Not running"
fi

echo ""
echo "Checking network interfaces..."

# Check AP interface
echo -n "Access Point Interface ($AP_INTERFACE): "
if ip addr show $AP_INTERFACE 2>/dev/null | grep -q "192.168.4.1"; then
    echo "✓ Configured with IP 192.168.4.1"
else
    echo "✗ Not properly configured"
fi

# Check WiFi client interface
echo -n "WiFi Client Interface ($WIFI_INTERFACE): "
if ip link show $WIFI_INTERFACE 2>/dev/null | grep -q "UP"; then
    echo "✓ Interface is up"
else
    echo "✗ Interface is down or not present"
fi

echo ""
echo "Testing web portal..."

# Test portal response
echo -n "Portal HTTP Response: "
if curl -s -o /dev/null -w '%{http_code}' http://localhost 2>/dev/null | grep -q "200"; then
    echo "✓ Portal responding (HTTP 200)"
else
    echo "✗ Portal not responding properly"
fi

echo ""
echo "Recent service logs:"
echo "==================="
if systemctl is-active --quiet travelnet 2>/dev/null; then
    journalctl -u travelnet --no-pager -n 5 2>/dev/null || echo "No logs available"
else
    echo "Service not running - no logs to display"
fi

echo ""
echo "Health check complete!"
echo ""
echo "If any services show as not running, try:"
echo "  sudo systemctl restart travelnet"
echo "  sudo systemctl restart hostapd"
echo "  sudo systemctl restart dnsmasq"
echo ""