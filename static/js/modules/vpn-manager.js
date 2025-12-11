// VPN Management Module
import ApiClient from '../utils/api-client.js';
import UIHelpers from './ui-helpers.js';

class VPNManager {
    constructor() {
        this.setupPeriodicStatusCheck();
        this.setupEventListeners();
    }

    setupPeriodicStatusCheck() {
        // Check VPN status every 30 seconds
        setInterval(() => this.checkVPNStatus(), 30000);
        
        // Check VPN status on page load
        document.addEventListener('DOMContentLoaded', () => {
            this.checkVPNStatus();
        });
    }

    setupEventListeners() {
        // Handle VPN config item clicks
        document.addEventListener('click', (e) => {
            // Handle connect button clicks
            if (e.target.closest('.connect-vpn-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const button = e.target.closest('.connect-vpn-btn');
                this.connectVPNInline(button);
                return;
            }
            
            // Handle VPN item expansion
            const vpnItem = e.target.closest('.vpn-config-item');
            if (vpnItem && !e.target.closest('.vpn-actions') && !e.target.closest('button')) {
                e.preventDefault();
                e.stopPropagation();
                this.toggleVPNExpansion(vpnItem);
            }
        });
    }

    toggleVPNExpansion(vpnItem) {
        const config = vpnItem.dataset.config;
        const isConnected = vpnItem.classList.contains('connected');
        
        // Close any other expanded items
        document.querySelectorAll('.vpn-config-item.expanded').forEach(item => {
            if (item !== vpnItem) {
                item.classList.remove('expanded');
                const actions = item.querySelector('.vpn-actions');
                if (actions) actions.remove();
            }
        });
        
        // Toggle current item
        if (vpnItem.classList.contains('expanded')) {
            vpnItem.classList.remove('expanded');
            const actions = vpnItem.querySelector('.vpn-actions');
            if (actions) actions.remove();
        } else {
            vpnItem.classList.add('expanded');
            this.addVPNActions(vpnItem, config, isConnected);
        }
    }

    addVPNActions(vpnItem, config, isConnected) {
        const actionsHtml = `
            <div class="vpn-actions mt-3 pt-3 border-top">
                <div class="d-flex gap-2">
                    ${!isConnected ? `
                        <button class="btn btn-success btn-sm connect-vpn-btn flex-grow-1" data-config="${config}">
                            <i class="fas fa-play me-1"></i>Connect
                        </button>
                    ` : `
                        <button class="btn btn-outline-danger btn-sm disconnect-vpn-btn flex-grow-1" onclick="disconnectVPN()">
                            <i class="fas fa-stop me-1"></i>Disconnect
                        </button>
                    `}
                    <button class="btn btn-outline-danger btn-sm" onclick="deleteConfig('${config}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
        
        vpnItem.insertAdjacentHTML('beforeend', actionsHtml);
    }

    async connectVPNInline(button) {
        const config = button.dataset.config;
        const originalText = button.innerHTML;
        
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Connecting...';
        button.disabled = true;
        
        try {
            await this.connectVPN(config);
            
            // Collapse the expanded item after successful connection
            const vpnItem = button.closest('.vpn-config-item');
            if (vpnItem) {
                vpnItem.classList.remove('expanded');
                const actions = vpnItem.querySelector('.vpn-actions');
                if (actions) actions.remove();
            }
        } catch (error) {
            console.error('Error connecting VPN:', error);
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }

    async toggleVPN() {
        try {
            const data = await ApiClient.get('/api/v1/vpn/status');
            
            if (data.success) {
                if (data.connected) {
                    await this.disconnectVPN();
                } else {
                    if (data.available_configs && data.available_configs.length > 0) {
                        await this.connectVPN(data.available_configs[0]);
                    } else {
                        UIHelpers.showNotification('No VPN configurations available. Please upload a configuration first.', 'warning');
                        window.location.href = '/vpn-tunnel';
                    }
                }
            } else {
                UIHelpers.showNotification('Failed to check VPN status', 'error');
            }
        } catch (error) {
            console.error('Error checking VPN status:', error);
            UIHelpers.showNotification('Failed to check VPN status', 'error');
        }
    }

    async connectVPN(configName) {
        if (!configName) return;
        
        const vpnToggleIcon = document.getElementById('vpnToggleIcon');
        const vpnToggleText = document.getElementById('vpnToggleText');
        
        // Show loading state
        if (vpnToggleIcon) {
            vpnToggleIcon.className = 'fas fa-spinner fa-spin fa-lg mb-1';
        }
        if (vpnToggleText) {
            vpnToggleText.textContent = 'Connecting...';
        }
        
        UIHelpers.showNotification('Connecting to VPN...', 'info');
        
        try {
            const data = { config_name: configName };
            const result = await ApiClient.post('/api/v1/vpn/connect', data);
            
            if (result.success) {
                UIHelpers.showNotification(result.message, 'success');
                this.updateVPNStatus(true);
            } else {
                UIHelpers.showNotification(result.message || 'Failed to connect to VPN', 'error');
                this.updateVPNStatus(false);
            }
        } catch (error) {
            console.error('Error connecting to VPN:', error);
            UIHelpers.showNotification('Failed to connect to VPN', 'error');
            this.updateVPNStatus(false);
        }
    }

    async disconnectVPN() {
        const vpnToggleIcon = document.getElementById('vpnToggleIcon');
        const vpnToggleText = document.getElementById('vpnToggleText');
        
        // Show loading state
        if (vpnToggleIcon) {
            vpnToggleIcon.className = 'fas fa-spinner fa-spin fa-lg mb-1';
        }
        if (vpnToggleText) {
            vpnToggleText.textContent = 'Disconnecting...';
        }
        
        UIHelpers.showNotification('Disconnecting from VPN...', 'info');
        
        try {
            const result = await ApiClient.post('/api/v1/vpn/disconnect');
            
            if (result.success) {
                UIHelpers.showNotification(result.message, 'success');
                this.updateVPNStatus(false);
            } else {
                UIHelpers.showNotification(result.message || 'Failed to disconnect from VPN', 'error');
                this.updateVPNStatus(true); // Assume still connected if disconnect failed
            }
        } catch (error) {
            console.error('Error disconnecting from VPN:', error);
            UIHelpers.showNotification('Failed to disconnect from VPN', 'error');
            this.updateVPNStatus(true); // Assume still connected if disconnect failed
        }
    }

    updateVPNStatus(connected) {
        const vpnToggleIcon = document.getElementById('vpnToggleIcon');
        const vpnToggleText = document.getElementById('vpnToggleText');
        const vpnBadge = document.getElementById('vpnBadge');
        
        if (vpnToggleIcon) {
            vpnToggleIcon.className = connected ? 'fas fa-toggle-on fa-lg mb-1' : 'fas fa-toggle-off fa-lg mb-1';
        }
        
        if (vpnToggleText) {
            vpnToggleText.textContent = connected ? 'VPN On' : 'VPN Off';
        }
        
        if (vpnBadge) {
            vpnBadge.style.display = connected ? 'inline-block' : 'none';
        }
    }

    async checkVPNStatus() {
        try {
            const data = await ApiClient.get('/api/v1/vpn/status');
            
            if (data.success) {
                this.updateVPNStatus(data.connected);
            }
        } catch (error) {
            console.error('Error checking VPN status:', error);
        }
    }
}

export default VPNManager;