// TravelNet Portal Main JavaScript

class TravelNetPortal {
    constructor() {
        this.isScanning = false;
        this.isConnecting = false;
        this.connectionCheckInterval = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.startConnectionMonitoring();
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
                this.connectToNetworkInline(networkItem);
                return;
            }
            
            // Handle network item expansion
            const networkItem = e.target.closest('.network-item');
            if (networkItem && !e.target.closest('.network-actions')) {
                console.log('Network item clicked:', networkItem.dataset.ssid);
                e.preventDefault();
                e.stopPropagation();
                this.toggleNetworkExpansion(networkItem);
            }
        });

        // No modal form submissions needed anymore

        const qrForm = document.getElementById('qrForm');
        if (qrForm) {
            qrForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.generateQRCode();
            });
        }

        // Security type change for QR form
        const qrSecurity = document.getElementById('qrSecurity');
        if (qrSecurity) {
            qrSecurity.addEventListener('change', () => {
                this.togglePasswordField();
            });
        }

        // Show/hide password
        const showPassword = document.getElementById('showPassword');
        if (showPassword) {
            showPassword.addEventListener('change', (e) => {
                const passwordField = document.getElementById('qrPassword');
                passwordField.type = e.target.checked ? 'text' : 'password';
            });
        }
    }

    async loadInitialData() {
        await this.updateConnectionStatus();
        await this.scanNetworks();
    }

    startConnectionMonitoring() {
        this.connectionCheckInterval = setInterval(() => {
            this.updateConnectionStatus();
        }, 10000); // Check every 10 seconds
    }

    async updateConnectionStatus() {
        try {
            const response = await fetch('/api/v1/networks/status');
            const data = await response.json();
            
            console.log('Connection status response:', data);
            
            if (data.success) {
                this.updateConnectionUI(data);
            }
        } catch (error) {
            console.error('Error updating connection status:', error);
        }
    }

    updateConnectionUI(status) {
        console.log('Updating connection UI with:', status);
        
        const connectionIcon = document.getElementById('connectionIcon');
        const connectionName = document.getElementById('connectionName');
        const connectionBadge = document.getElementById('connectionBadge');
        const connectionSignal = document.getElementById('connectionSignal');

        console.log('Elements found:', {
            connectionIcon: !!connectionIcon,
            connectionName: !!connectionName,
            connectionBadge: !!connectionBadge,
            connectionSignal: !!connectionSignal
        });

        if (!connectionIcon || !connectionName || !connectionBadge) return;

        if (status.connected && status.current_network) {
            const network = status.current_network;
            
            console.log('Connected to network:', network);
            
            connectionIcon.innerHTML = '<i class="fas fa-wifi text-success fa-lg"></i>';
            connectionName.textContent = network.ssid;
            connectionBadge.textContent = 'Connected';
            connectionBadge.className = 'status-badge connected';
            
            if (connectionSignal) {
                console.log('Signal strength:', network.signal_strength);
                connectionSignal.innerHTML = this.getSignalBars(network.signal_strength);
            }
        } else {
            console.log('Not connected');
            
            connectionIcon.innerHTML = '<i class="fas fa-wifi-slash text-danger fa-lg"></i>';
            connectionName.textContent = 'Not Connected';
            connectionBadge.textContent = 'Disconnected';
            connectionBadge.className = 'status-badge disconnected';
            
            if (connectionSignal) {
                connectionSignal.innerHTML = '<i class="fas fa-question text-secondary"></i>';
            }
        }
    }

    async scanNetworks() {
        if (this.isScanning) return;
        
        this.isScanning = true;
        this.showScanningState();

        try {
            const response = await fetch('/api/v1/networks/scan');
            const data = await response.json();
            
            if (data.success) {
                this.displayNetworks(data.networks);
            } else {
                this.showError('Failed to scan networks: ' + data.message);
            }
        } catch (error) {
            console.error('Error scanning networks:', error);
            this.showError('Network scan failed');
        } finally {
            this.isScanning = false;
            this.hideScanningState();
        }
    }

    showScanningState() {
        const scanButtons = document.querySelectorAll('[onclick="scanNetworks()"]');
        scanButtons.forEach(btn => {
            btn.classList.add('loading');
            btn.disabled = true;
        });
    }

    hideScanningState() {
        const scanButtons = document.querySelectorAll('[onclick="scanNetworks()"]');
        scanButtons.forEach(btn => {
            btn.classList.remove('loading');
            btn.disabled = false;
        });
    }

    displayNetworks(networks) {
        const networksList = document.getElementById('networksList');
        if (!networksList) return;

        if (networks.length === 0) {
            networksList.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-search fa-2x mb-3"></i>
                    <p>No networks found. Try scanning again.</p>
                </div>
            `;
            return;
        }

        // Get current connection status to mark connected networks
        this.getCurrentConnectionSSID().then(currentSSID => {
            networksList.innerHTML = networks.map(network => {
                const isConnected = currentSSID && network.ssid === currentSSID;
                return `
                    <div class="network-item ${isConnected ? 'connected' : ''}" 
                         data-ssid="${network.ssid}" 
                         data-security="${network.security}">
                        <div class="network-main d-flex justify-content-between align-items-center">
                            <div class="flex-grow-1">
                                <div class="network-name">
                                    ${network.ssid}
                                    ${isConnected ? '<span class="badge bg-success ms-2">Connected</span>' : ''}
                                </div>
                                <div class="network-security">
                                    <i class="fas fa-${network.security === 'Open' ? 'unlock' : 'lock'} me-1"></i>
                                    ${network.security}
                                </div>
                            </div>
                            <div class="d-flex align-items-center gap-2">
                                <div class="signal-strength">
                                    ${this.getSignalBars(network.signal_strength)}
                                </div>
                                <div class="expand-indicator">
                                    <i class="fas fa-chevron-down"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        });
    }

    async getCurrentConnectionSSID() {
        try {
            const response = await fetch('/api/v1/networks/status');
            const data = await response.json();
            
            if (data.success && data.connected && data.current_network) {
                return data.current_network.ssid;
            }
            return null;
        } catch (error) {
            console.error('Error getting current connection:', error);
            return null;
        }
    }

    getSignalClass(strength) {
        // Handle both percentage (0-100) and dBm (-30 to -90) values
        if (strength > 0) {
            // Percentage values (0-100)
            if (strength >= 80) return 'signal-excellent';
            if (strength >= 60) return 'signal-good';
            if (strength >= 40) return 'signal-fair';
            return 'signal-poor';
        } else {
            // dBm values (negative)
            if (strength >= -50) return 'signal-excellent';
            if (strength >= -60) return 'signal-good';
            if (strength >= -70) return 'signal-fair';
            return 'signal-poor';
        }
    }

    getSignalBars(strength) {
        let bars = 0;
        let color = 'text-danger';
        
        // Handle both percentage (0-100) and dBm (-30 to -90) values
        if (strength > 0) {
            // Percentage values (0-100)
            if (strength >= 80) { bars = 4; color = 'text-success'; }
            else if (strength >= 60) { bars = 3; color = 'text-success'; }
            else if (strength >= 40) { bars = 2; color = 'text-warning'; }
            else if (strength >= 20) { bars = 1; color = 'text-warning'; }
            else { bars = 1; color = 'text-danger'; }
        } else {
            // dBm values (negative)
            if (strength >= -50) { bars = 4; color = 'text-success'; }
            else if (strength >= -60) { bars = 3; color = 'text-success'; }
            else if (strength >= -70) { bars = 2; color = 'text-warning'; }
            else if (strength >= -80) { bars = 1; color = 'text-warning'; }
            else { bars = 1; color = 'text-danger'; }
        }
        
        // Create signal bars HTML
        let barsHtml = '<div class="signal-bars">';
        for (let i = 1; i <= 4; i++) {
            const barClass = i <= bars ? color : 'text-muted';
            const opacity = i <= bars ? '1' : '0.3';
            barsHtml += `<div class="signal-bar bar-${i} ${barClass}" style="opacity: ${opacity}"></div>`;
        }
        barsHtml += '</div>';
        
        return barsHtml;
    }

    toggleNetworkExpansion(networkItem) {
        const ssid = networkItem.dataset.ssid;
        const security = networkItem.dataset.security;
        const isConnected = networkItem.classList.contains('connected');
        
        console.log('Toggling expansion for network:', ssid, 'Security:', security, 'Connected:', isConnected);
        
        // Close any other expanded items
        document.querySelectorAll('.network-item.expanded').forEach(item => {
            if (item !== networkItem) {
                item.classList.remove('expanded');
                const actions = item.querySelector('.network-actions');
                if (actions) actions.remove();
            }
        });
        
        // Toggle current item
        if (networkItem.classList.contains('expanded')) {
            networkItem.classList.remove('expanded');
            const actions = networkItem.querySelector('.network-actions');
            if (actions) actions.remove();
        } else {
            networkItem.classList.add('expanded');
            this.addNetworkActions(networkItem, ssid, security, isConnected);
        }
    }

    addNetworkActions(networkItem, ssid, security, isConnected) {
        const actionsHtml = `
            <div class="network-actions mt-3 pt-3 border-top">
                ${security !== 'Open' && !isConnected ? `
                    <div class="mb-3">
                        <input type="password" 
                               class="form-control form-control-sm" 
                               placeholder="Enter password (leave empty to use saved password)"
                               data-network="${ssid}">
                    </div>
                ` : ''}
                <div class="d-flex gap-2">
                    <button class="btn ${isConnected ? 'btn-outline-danger' : 'btn-primary'} btn-sm connect-btn flex-grow-1" data-network="${ssid}" data-action="${isConnected ? 'disconnect' : 'connect'}">
                        <i class="fas fa-${isConnected ? 'unlink' : 'plug'} me-1"></i>
                        ${isConnected ? 'Disconnect' : 'Connect'}
                        <span class="spinner-border spinner-border-sm ms-2" style="display: none;"></span>
                    </button>
                </div>
            </div>
        `;
        
        networkItem.insertAdjacentHTML('beforeend', actionsHtml);
        
        // Focus password field if it exists and not connected
        const passwordField = networkItem.querySelector('input[type="password"]');
        if (passwordField && !isConnected) {
            setTimeout(() => passwordField.focus(), 100);
        }
    }

    async connectToNetworkInline(networkItem) {
        if (this.isConnecting) return;

        const ssid = networkItem.dataset.ssid;
        const connectBtn = networkItem.querySelector('.connect-btn');
        const action = connectBtn.dataset.action;
        const passwordField = networkItem.querySelector('input[type="password"]');
        const password = passwordField ? passwordField.value : '';
        
        this.isConnecting = true;
        const originalText = connectBtn.innerHTML;
        
        if (action === 'disconnect') {
            connectBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Disconnecting...';
        } else {
            connectBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Connecting...';
        }
        connectBtn.disabled = true;

        try {
            let response, result;
            
            if (action === 'disconnect') {
                // Disconnect from network
                response = await fetch('/api/v1/networks/disconnect', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                result = await response.json();
                
                if (result.success) {
                    this.showSuccess(`Disconnected from ${ssid}!`);
                } else {
                    this.showError('Disconnection failed: ' + result.message);
                }
            } else {
                // Connect to network
                const data = {
                    ssid: ssid,
                    password: password || ''
                };

                response = await fetch('/api/v1/networks/connect', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                result = await response.json();
                
                if (result.success) {
                    this.showSuccess(`Connected to ${ssid}!`);
                } else {
                    this.showError('Connection failed: ' + result.message);
                }
            }
            
            if (result.success) {
                // Collapse the expanded item
                networkItem.classList.remove('expanded');
                const actions = networkItem.querySelector('.network-actions');
                if (actions) actions.remove();
                
                setTimeout(() => {
                    this.updateConnectionStatus();
                    this.scanNetworks();
                }, 1000);
            }
            
        } catch (error) {
            console.error('Error with network operation:', error);
            this.showError('Network operation failed');
        } finally {
            this.isConnecting = false;
            connectBtn.innerHTML = originalText;
            connectBtn.disabled = false;
        }
    }

    // Keep the old method for backward compatibility but make it call the inline version
    async connectToNetwork() {
        // This method is kept for any remaining modal-based calls
        console.warn('connectToNetwork called - this should use connectToNetworkInline instead');
    }

    async disconnectFromNetwork() {
        if (this.isConnecting) return;

        // Confirm disconnection
        if (!confirm('Are you sure you want to disconnect from the current network?')) {
            return;
        }

        this.isConnecting = true;
        const disconnectBtn = document.getElementById('disconnectBtn');
        const originalHTML = disconnectBtn.innerHTML;
        
        disconnectBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
        disconnectBtn.disabled = true;

        try {
            const response = await fetch('/api/v1/networks/disconnect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('Disconnected successfully!');
                setTimeout(() => {
                    this.updateConnectionStatus();
                    this.scanNetworks();
                }, 1000);
            } else {
                this.showError('Disconnection failed: ' + result.message);
            }
        } catch (error) {
            console.error('Error disconnecting from network:', error);
            this.showError('Disconnection failed');
        } finally {
            this.isConnecting = false;
            disconnectBtn.innerHTML = originalHTML;
            disconnectBtn.disabled = false;
        }
    }

    togglePasswordField() {
        const security = document.getElementById('qrSecurity').value;
        const passwordField = document.getElementById('passwordField');
        
        if (security === 'nopass') {
            passwordField.style.display = 'none';
        } else {
            passwordField.style.display = 'block';
        }
    }

    async generateQRCode() {
        const ssid = document.getElementById('qrSSID').value;
        const password = document.getElementById('qrPassword').value;
        const security = document.getElementById('qrSecurity').value;

        if (!ssid.trim()) {
            this.showError('Please enter a network name');
            return;
        }

        const submitBtn = document.querySelector('#qrForm button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generating...';
        submitBtn.disabled = true;

        try {
            const response = await fetch('/api/v1/qr/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ssid: ssid,
                    password: password,
                    security: security
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.displayQRCode(result.qr_code, ssid);
            } else {
                this.showError('QR generation failed: ' + result.message);
            }
        } catch (error) {
            console.error('Error generating QR code:', error);
            this.showError('QR generation failed');
        } finally {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }

    displayQRCode(qrCodeData, ssid) {
        const qrResult = document.getElementById('qrResult');
        if (!qrResult) return;

        qrResult.innerHTML = `
            <div class="qr-container fade-in">
                <h5 class="mb-3">QR Code Generated</h5>
                <img src="data:image/png;base64,${qrCodeData}" alt="WiFi QR Code" class="qr-code">
                <p class="text-muted mt-3">
                    <strong>Network:</strong> ${ssid}<br>
                    Scan this QR code with your phone's camera to connect automatically.
                </p>
                <button class="btn btn-outline-primary btn-custom" onclick="portal.downloadQRCode('${ssid}')">
                    <i class="fas fa-download me-2"></i>Download QR Code
                </button>
            </div>
        `;
        
        qrResult.scrollIntoView({ behavior: 'smooth' });
    }

    downloadQRCode(ssid) {
        const qrImage = document.querySelector('.qr-code');
        if (!qrImage) return;

        const link = document.createElement('a');
        link.download = `wifi-qr-${ssid || 'network'}.png`;
        link.href = qrImage.src;
        link.click();
    }

    printQRCode() {
        const qrImage = document.querySelector('.qr-code');
        if (!qrImage) return;

        const printWindow = window.open('', '_blank');
        const ssid = document.getElementById('qrSSID')?.value || 'Network';
        
        printWindow.document.write(`
            <html>
                <head>
                    <title>WiFi QR Code</title>
                    <style>
                        body { 
                            display: flex; 
                            justify-content: center; 
                            align-items: center; 
                            min-height: 100vh; 
                            margin: 0; 
                            font-family: Arial, sans-serif;
                        }
                        .print-container {
                            text-align: center;
                        }
                        img {
                            max-width: 400px;
                            height: auto;
                        }
                        h2 {
                            margin-bottom: 20px;
                            color: #333;
                        }
                        p {
                            margin-top: 20px;
                            color: #666;
                            font-size: 14px;
                        }
                    </style>
                </head>
                <body>
                    <div class="print-container">
                        <h2>WiFi QR Code</h2>
                        <img src="${qrImage.src}" alt="WiFi QR Code">
                        <p>Scan with your phone's camera to connect</p>
                        <p>Network: ${ssid}</p>
                    </div>
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }

    clearQRForm() {
        document.getElementById('qrForm').reset();
        const qrResult = document.getElementById('qrResult');
        if (qrResult) qrResult.style.display = 'none';
        
        const passwordField = document.getElementById('passwordField');
        if (passwordField) passwordField.style.display = 'block';
    }

    quickConnect(ssid, password, security) {
        const ssidField = document.getElementById('qrSSID');
        const passwordField = document.getElementById('qrPassword');
        const securityField = document.getElementById('qrSecurity');
        
        if (ssidField) ssidField.value = ssid;
        if (passwordField) passwordField.value = password;
        if (securityField) {
            securityField.value = security;
            securityField.dispatchEvent(new Event('change'));
        }
        
        // Auto-generate QR code
        this.generateQRCode();
    }

    focusSSIDField() {
        const ssidField = document.getElementById('qrSSID');
        if (ssidField) {
            ssidField.focus();
            this.showAlert('Enter your custom network details above', 'info');
        }
    }

    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    showError(message) {
        this.showAlert(message, 'danger');
    }

    showAlert(message, type) {
        const alertContainer = document.getElementById('alertContainer') || document.body;
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show alert-custom`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertContainer.appendChild(alert);
        
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
}

// Global functions for backward compatibility
function scanNetworks() {
    if (window.portal) {
        window.portal.scanNetworks();
    }
}

function connectToNetwork() {
    if (window.portal) {
        window.portal.connectToNetwork();
    }
}

function generateQRCode() {
    if (window.portal) {
        window.portal.generateQRCode();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.portal = new TravelNetPortal();
});