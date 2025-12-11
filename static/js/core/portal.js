// TravelNet Portal Main Class
import NetworkManager from '../modules/network-manager.js';
import QRGenerator from '../modules/qr-generator.js';
import VPNManager from '../modules/vpn-manager.js';

class TravelNetPortal {
    constructor() {
        this.networkManager = new NetworkManager();
        this.qrGenerator = new QRGenerator();
        this.vpnManager = new VPNManager();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.networkManager.startConnectionMonitoring();
        this.loadInitialData();
    }

    setupEventListeners() {
        // Network item clicks
        document.addEventListener('click', (e) => {
            // Handle connect button clicks
            if (e.target.closest('.connect-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const networkItem = e.target.closest('.network-item');
                this.networkManager.connectToNetworkInline(networkItem);
                return;
            }
            
            // Handle network item expansion
            const networkItem = e.target.closest('.network-item');
            if (networkItem && !e.target.closest('.network-actions')) {
                console.log('Network item clicked:', networkItem.dataset.ssid);
                e.preventDefault();
                e.stopPropagation();
                this.networkManager.toggleNetworkExpansion(networkItem);
            }
        });
    }

    async loadInitialData() {
        await this.networkManager.updateConnectionStatus();
        await this.networkManager.scanNetworks();
    }

    // Expose methods for backward compatibility
    async scanNetworks() {
        return this.networkManager.scanNetworks();
    }

    async connectToNetwork() {
        return this.networkManager.connectToNetwork();
    }

    async generateQRCode() {
        return this.qrGenerator.generateQRCode();
    }

    toggleVPN() {
        return this.vpnManager.toggleVPN();
    }
}

export default TravelNetPortal;