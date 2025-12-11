// Network Management Module
import ApiClient from '../utils/api-client.js';
import { showAlert, setLoadingState } from './ui-helpers.js';
import UIHelpers from './ui-helpers.js';

class NetworkManager {
    constructor() {
        this.isScanning = false;
        this.isConnecting = false;
        this.connectionCheckInterval = null;
    }

    startConnectionMonitoring() {
        this.connectionCheckInterval = setInterval(() => {
            this.updateConnectionStatus();
        }, 10000); // Check every 10 seconds
    }

    async updateConnectionStatus() {
        try {
            const data = await ApiClient.get('/api/v1/networks/status');
            
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

        if (!connectionIcon || !connectionName || !connectionBadge) return;

        if (status.connected && status.current_network) {
            const network = status.current_network;
            
            connectionIcon.innerHTML = '<i class="fas fa-wifi text-success fa-lg"></i>';
            connectionName.textContent = network.ssid;
            connectionBadge.innerHTML = '<i class="fas fa-wifi me-1"></i>Connected';
            connectionBadge.className = 'status-badge connected';
            
            if (connectionSignal) {
                connectionSignal.innerHTML = UIHelpers.getSignalBars(network.signal_strength);
            }
        } else {
            connectionIcon.innerHTML = '<i class="fas fa-wifi-slash text-danger fa-lg"></i>';
            connectionName.textContent = 'Not Connected';
            connectionBadge.innerHTML = '<i class="fas fa-wifi-slash me-1"></i>Disconnected';
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
            const data = await ApiClient.get('/api/v1/networks/scan');
            
            if (data.success) {
                this.displayNetworks(data.networks);
            } else {
                showAlert('Failed to scan networks: ' + (data.message || 'Unknown error'), 'danger');
            }
        } catch (error) {
            console.error('Error scanning networks:', error);
            showAlert('Network scan failed', 'danger');
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

    async displayNetworks(networks) {
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
        const currentSSID = await this.getCurrentConnectionSSID();
        
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
                                ${UIHelpers.getSignalBars(network.signal_strength)}
                            </div>
                            <div class="expand-indicator">
                                <i class="fas fa-chevron-down"></i>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    async getCurrentConnectionSSID() {
        try {
            const data = await ApiClient.get('/api/v1/networks/status');
            
            if (data.success && data.connected && data.current_network) {
                return data.current_network.ssid;
            }
            return null;
        } catch (error) {
            console.error('Error getting current connection:', error);
            return null;
        }
    }

    toggleNetworkExpansion(networkItem) {
        const ssid = networkItem.dataset.ssid;
        const security = networkItem.dataset.security;
        const isConnected = networkItem.classList.contains('connected');
        
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
        
        UIHelpers.setLoadingState(connectBtn, true, 
            action === 'disconnect' ? 'Disconnecting...' : 'Connecting...');

        try {
            let result;
            
            if (action === 'disconnect') {
                result = await ApiClient.post('/api/v1/networks/disconnect');
                
                if (result.success) {
                    showAlert(`Disconnected from ${ssid}!`, 'success');
                } else {
                    showAlert('Disconnection failed: ' + (result.message || 'Unknown error'), 'danger');
                }
            } else {
                const data = { ssid: ssid, password: password || '' };
                result = await ApiClient.post('/api/v1/networks/connect', data);
                
                if (result.success) {
                    showAlert(`Connected to ${ssid}!`, 'success');
                } else {
                    showAlert('Connection failed: ' + (result.message || 'Unknown error'), 'danger');
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
            showAlert('Network operation failed', 'danger');
        } finally {
            this.isConnecting = false;
            setLoadingState(connectBtn, false, originalText);
        }
    }

    async disconnectFromNetwork() {
        if (this.isConnecting) return;

        if (!confirm('Are you sure you want to disconnect from the current network?')) {
            return;
        }

        this.isConnecting = true;
        const disconnectBtn = document.getElementById('disconnectBtn');
        
        setLoadingState(disconnectBtn, true);

        try {
            const result = await ApiClient.post('/api/v1/networks/disconnect');
            
            if (result.success) {
                showAlert('Disconnected successfully!', 'success');
                setTimeout(() => {
                    this.updateConnectionStatus();
                    this.scanNetworks();
                }, 1000);
            } else {
                showAlert('Disconnection failed: ' + (result.message || 'Unknown error'), 'danger');
            }
        } catch (error) {
            console.error('Error disconnecting from network:', error);
            showAlert('Disconnection failed', 'danger');
        } finally {
            this.isConnecting = false;
            setLoadingState(disconnectBtn, false);
        }
    }
}

export default NetworkManager;