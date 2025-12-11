/**
 * System Settings Module
 * 
 * Handles system settings page functionality including:
 * - Hotspot configuration management
 * - Network service restart
 * - System reboot
 * - System status monitoring
 * - System logs viewing
 */

import { showAlert, showLoading, hideLoading, setLoadingState, formatBytes, formatUptime } from './ui-helpers.js';

class SystemSettingsManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadInitialData();
    }

    bindEvents() {
        // Hotspot form submission
        const hotspotForm = document.getElementById('hotspotForm');
        if (hotspotForm) {
            hotspotForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.updateHotspotConfig();
            });
        }

        // Password visibility toggle
        const togglePassword = document.getElementById('togglePassword');
        if (togglePassword) {
            togglePassword.addEventListener('click', () => {
                this.togglePasswordVisibility();
            });
        }

        // Auto-refresh system status every 30 seconds
        setInterval(() => {
            this.refreshSystemStatus();
        }, 30000);
    }

    async loadInitialData() {
        await Promise.all([
            this.loadCurrentHotspotSettings(),
            this.refreshSystemStatus()
        ]);
    }

    async loadCurrentHotspotSettings() {
        try {
            console.log('Loading hotspot settings...');
            const response = await fetch('/api/v1/hotspot/config');
            console.log('Hotspot config response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('Hotspot config data:', data);
            
            if (data.success && data.config) {
                this.populateHotspotForm(data.config);
                console.log('Hotspot form populated with:', data.config);
            } else {
                console.warn('Could not load current hotspot settings:', data.message || data.error);
                // Don't show error alert on page load, just log it
            }
        } catch (error) {
            console.error('Error loading hotspot settings:', error);
            // Don't show error alert on page load, just log it
        }
    }

    populateHotspotForm(config) {
        const form = document.getElementById('hotspotForm');
        if (!form) return;

        // Populate form fields
        const ssidInput = form.querySelector('#hotspotSSID');
        const passwordInput = form.querySelector('#hotspotPassword');
        const visibleCheckbox = form.querySelector('#hotspotVisible');
        const enabledCheckbox = form.querySelector('#hotspotEnabled');

        if (ssidInput) ssidInput.value = config.ssid || '';
        if (passwordInput) passwordInput.value = config.password || '';
        if (visibleCheckbox) visibleCheckbox.checked = config.visible !== false;
        if (enabledCheckbox) enabledCheckbox.checked = config.enabled !== false;
    }

    async updateHotspotConfig() {
        const form = document.getElementById('hotspotForm');
        if (!form) return;

        const formData = new FormData(form);
        const config = {
            ssid: formData.get('ssid').trim(),
            password: formData.get('password').trim(),
            visible: formData.has('visible'),
            enabled: formData.has('enabled')
        };

        // Validation
        if (!config.ssid) {
            showAlert('Hotspot SSID is required', 'warning');
            return;
        }

        if (config.ssid.length > 32) {
            showAlert('Hotspot SSID must be 32 characters or less', 'warning');
            return;
        }

        if (config.password && (config.password.length < 8 || config.password.length > 63)) {
            showAlert('Password must be between 8 and 63 characters, or empty for open network', 'warning');
            return;
        }

        const submitBtn = form.querySelector('button[type="submit"]');
        setLoadingState(submitBtn, true);

        try {
            // First test if we can reach the GET endpoint
            console.log('Testing GET request first...');
            const testResponse = await fetch('/api/v1/hotspot/config');
            console.log('GET test response:', testResponse.status);
            
            if (testResponse.ok) {
                showAlert(`DEBUG: GET works. POST data: ${JSON.stringify(config)}`, 'info');
            } else {
                showAlert(`DEBUG: GET request failed with ${testResponse.status}`, 'warning');
            }

            console.log('Making hotspot config POST request with data:', config);
            const response = await fetch('/api/v1/hotspot/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            console.log('POST Response received:', response.status);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('Response data:', data);

            if (data.success) {
                showAlert('Hotspot configuration updated successfully', 'success');
                setTimeout(() => this.refreshSystemStatus(), 2000);
            } else {
                showAlert('Failed to update hotspot configuration: ' + (data.message || 'Unknown error'), 'danger');
            }
        } catch (error) {
            console.error('Error updating hotspot config:', error);
            showAlert('DEBUG: Error details - ' + error.message, 'danger');
        }
        
        setLoadingState(submitBtn, false);
    }

    togglePasswordVisibility() {
        const passwordInput = document.getElementById('hotspotPassword');
        const toggleBtn = document.getElementById('togglePassword');
        
        if (!passwordInput || !toggleBtn) return;

        const icon = toggleBtn.querySelector('i');
        
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            icon.className = 'fas fa-eye-slash';
        } else {
            passwordInput.type = 'password';
            icon.className = 'fas fa-eye';
        }
    }

    async refreshSystemStatus() {
        const container = document.getElementById('systemStatusContent');
        if (!container) {
            console.error('System status container not found');
            return;
        }

        try {
            console.log('Fetching system status...');
            const response = await fetch('/api/v1/system/status');
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('System status data:', data);

            if (data.success) {
                this.updateSystemStatusDisplay(data);
            } else {
                console.error('Failed to get system status:', data.message || data.error);
                container.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Could not load system status: ${data.message || data.error || 'Unknown error'}
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error refreshing system status:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Failed to load system status: ${error.message}
                </div>
            `;
        }
    }

    updateSystemStatusDisplay(status) {
        const container = document.getElementById('systemStatusContent');
        if (!container) return;

        const services = status.services || {};
        const system = status.system || {};

        container.innerHTML = `
            <div class="row g-3">
                <div class="col-md-6">
                    <div class="status-item">
                        <div class="d-flex justify-content-between align-items-center">
                            <span><i class="fas fa-network-wired me-2"></i>Network Manager</span>
                            <span class="badge ${services.network_manager?.active ? 'bg-success' : 'bg-danger'}">
                                ${services.network_manager?.active ? 'Active' : 'Inactive'}
                            </span>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="status-item">
                        <div class="d-flex justify-content-between align-items-center">
                            <span><i class="fas fa-terminal me-2"></i>SSH Service</span>
                            <span class="badge ${services.ssh?.active ? 'bg-success' : 'bg-danger'}">
                                ${services.ssh?.active ? 'Active' : 'Inactive'}
                            </span>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="status-item">
                        <div class="d-flex justify-content-between align-items-center">
                            <span><i class="fas fa-clock me-2"></i>Uptime</span>
                            <span class="text-muted">${system.uptime || 'Unknown'}</span>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="status-item">
                        <div class="d-flex justify-content-between align-items-center">
                            <span><i class="fas fa-memory me-2"></i>Memory Usage</span>
                            <span class="text-muted">
                                ${system.memory?.usage_percent || 0}%
                                ${system.memory?.used_mb ? `(${system.memory.used_mb}MB)` : ''}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="mt-3 text-muted small">
                <i class="fas fa-info-circle me-1"></i>
                Last updated: ${new Date().toLocaleTimeString()}
            </div>
        `;
    }

    async restartNetwork() {
        if (!confirm('Are you sure you want to restart network services? This may temporarily interrupt connections.')) {
            return;
        }

        const btn = event.target.closest('button');
        try {
            setLoadingState(btn, true);

            const response = await fetch('/api/v1/system/restart-network', {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                showAlert(data.message || 'Network services restarted successfully', 'success');
                // Refresh status after a delay
                setTimeout(() => this.refreshSystemStatus(), 5000);
            } else {
                showAlert(data.message || 'Failed to restart network services', 'danger');
            }
        } catch (error) {
            console.error('Error restarting network:', error);
            showAlert('Failed to restart network services', 'danger');
        } finally {
            setLoadingState(btn, false);
        }
    }

    async rebootSystem() {
        if (!confirm('Are you sure you want to reboot the system? This will disconnect all users and restart the router.')) {
            return;
        }

        if (!confirm('This action cannot be undone. The system will be unavailable for 1-2 minutes. Continue?')) {
            return;
        }

        const btn = event.target.closest('button');
        try {
            setLoadingState(btn, true);

            const response = await fetch('/api/v1/system/reboot', {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                showAlert('System reboot initiated. The router will be back online in 1-2 minutes.', 'info');
                // Disable all buttons to prevent further actions
                document.querySelectorAll('button').forEach(button => {
                    button.disabled = true;
                });
            } else {
                showAlert(data.message || 'Failed to reboot system', 'danger');
                setLoadingState(btn, false);
            }
        } catch (error) {
            console.error('Error rebooting system:', error);
            showAlert('Failed to reboot system', 'danger');
            setLoadingState(btn, false);
        }
    }

    async viewSystemLogs() {
        const logsSection = document.getElementById('systemLogsSection');
        if (!logsSection) {
            console.error('System logs section not found');
            showAlert('System logs section not available', 'danger');
            return;
        }

        // Show the logs section
        logsSection.style.display = 'block';
        
        // Scroll to the logs section
        logsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        // Load initial logs
        await this.loadSystemLogs();
    }

    hideSystemLogs() {
        const logsSection = document.getElementById('systemLogsSection');
        if (logsSection) {
            logsSection.style.display = 'none';
        }
    }

    async loadSystemLogs() {
        const logType = document.getElementById('logTypeSelect')?.value || 'application';
        const container = document.getElementById('systemLogsContent');
        
        if (!container) return;

        try {
            container.innerHTML = `
                <div class="text-center text-muted py-3">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2 mb-0">Loading ${logType} logs...</p>
                </div>
            `;

            const response = await fetch(`/api/v1/system/logs?type=${logType}&lines=100`);
            const data = await response.json();

            if (data.success) {
                const logs = data.logs || 'No logs available';
                container.innerHTML = `
                    <pre class="log-viewer">${this.escapeHtml(logs)}</pre>
                `;
                
                // Auto-scroll to bottom
                const logViewer = container.querySelector('.log-viewer');
                if (logViewer) {
                    logViewer.scrollTop = logViewer.scrollHeight;
                }
            } else {
                container.innerHTML = `
                    <div class="alert alert-warning m-3">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        ${data.error || 'Failed to load logs'}
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error loading system logs:', error);
            container.innerHTML = `
                <div class="alert alert-danger m-3">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Failed to load system logs
                </div>
            `;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global functions for template compatibility
window.loadCurrentHotspotSettings = () => {
    if (window.systemSettingsManager) {
        window.systemSettingsManager.loadCurrentHotspotSettings();
    }
};

window.restartNetwork = () => {
    if (window.systemSettingsManager) {
        window.systemSettingsManager.restartNetwork();
    }
};

window.refreshNetworkStatus = () => {
    if (window.systemSettingsManager) {
        window.systemSettingsManager.refreshSystemStatus();
    }
};

window.rebootSystem = () => {
    if (window.systemSettingsManager) {
        window.systemSettingsManager.rebootSystem();
    }
};

window.refreshSystemStatus = () => {
    if (window.systemSettingsManager) {
        window.systemSettingsManager.refreshSystemStatus();
    }
};

window.viewSystemLogs = () => {
    if (window.systemSettingsManager) {
        window.systemSettingsManager.viewSystemLogs();
    }
};

window.loadSystemLogs = () => {
    if (window.systemSettingsManager) {
        window.systemSettingsManager.loadSystemLogs();
    }
};

window.hideSystemLogs = () => {
    if (window.systemSettingsManager) {
        window.systemSettingsManager.hideSystemLogs();
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.systemSettingsManager = new SystemSettingsManager();
});

export default SystemSettingsManager;