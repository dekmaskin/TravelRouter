// UI Helper Functions
class UIHelpers {
    static showSuccess(message) {
        this.showAlert(message, 'success');
    }

    static showError(message) {
        this.showAlert(message, 'danger');
    }

    static showAlert(message, type) {
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

    static showNotification(message, type) {
        // Alias for showAlert for backward compatibility
        this.showAlert(message, type === 'error' ? 'danger' : type);
    }

    static setLoadingState(element, isLoading, originalText = '') {
        if (isLoading) {
            element.dataset.originalText = element.innerHTML;
            element.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
            element.disabled = true;
        } else {
            element.innerHTML = element.dataset.originalText || originalText;
            element.disabled = false;
        }
    }

    static showLoading(message = 'Loading...', element = null) {
        if (element) {
            // Show loading on specific element
            this.setLoadingState(element, true);
        } else {
            // Show global loading overlay
            const overlay = document.getElementById('loadingOverlay');
            if (overlay) {
                const messageElement = overlay.querySelector('p');
                if (messageElement) {
                    messageElement.textContent = message;
                }
                overlay.style.display = 'flex';
            }
        }
    }

    static hideLoading(element = null) {
        if (element) {
            // Hide loading on specific element
            this.setLoadingState(element, false);
        } else {
            // Hide global loading overlay
            const overlay = document.getElementById('loadingOverlay');
            if (overlay) {
                overlay.style.display = 'none';
            }
        }
    }

    static getSignalBars(strength) {
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
}

// Export individual functions for convenience
export const showAlert = (type, message) => UIHelpers.showAlert(message, type);
export const showLoading = (message, element) => UIHelpers.showLoading(message, element);
export const hideLoading = (element) => UIHelpers.hideLoading(element);
export const setLoadingState = (element, isLoading, originalText) => UIHelpers.setLoadingState(element, isLoading, originalText);
export const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};
export const formatUptime = (seconds) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
};

export default UIHelpers;