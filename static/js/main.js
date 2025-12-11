// TravelNet Portal - Main Entry Point
import TravelNetPortal from './core/portal.js';

// Global instances
let portal, networkManager, qrGenerator, vpnManager;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    portal = new TravelNetPortal();
    
    // Expose instances globally for backward compatibility
    window.portal = portal;
    window.networkManager = portal.networkManager;
    window.qrGenerator = portal.qrGenerator;
    window.vpnManager = portal.vpnManager;
    
    // Initialize footer time display
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000); // Update every second
});

// Update current time in footer
function updateCurrentTime() {
    const timeElement = document.getElementById('currentTime');
    if (timeElement) {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        timeElement.textContent = timeString;
    }
}

// Global functions for backward compatibility
window.scanNetworks = () => portal?.scanNetworks();
window.connectToNetwork = () => portal?.connectToNetwork();
window.generateQRCode = () => portal?.generateQRCode();
window.toggleVPN = () => portal?.toggleVPN();
window.connectVPN = (configName) => vpnManager?.connectVPN(configName);
window.disconnectVPN = () => vpnManager?.disconnectVPN();
window.updateVPNStatus = (connected) => vpnManager?.updateVPNStatus(connected);
window.checkVPNStatus = () => vpnManager?.checkVPNStatus();