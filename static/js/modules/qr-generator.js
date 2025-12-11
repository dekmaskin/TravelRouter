// QR Code Generation Module
import ApiClient from '../utils/api-client.js';
import { showAlert, setLoadingState } from './ui-helpers.js';
import UIHelpers from './ui-helpers.js';

class QRGenerator {
    constructor() {
        this.setupEventListeners();
    }

    setupEventListeners() {
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
            showAlert('Please enter a network name', 'warning');
            return;
        }

        const submitBtn = document.querySelector('#qrForm button[type="submit"]');
        setLoadingState(submitBtn, true, 'Generating...');

        try {
            const data = { ssid, password, security };
            const result = await ApiClient.post('/api/v1/qr/generate', data);
            
            if (result.success) {
                this.displayQRCode(result.qr_code, ssid);
            } else {
                showAlert('QR generation failed: ' + (result.message || 'Unknown error'), 'danger');
            }
        } catch (error) {
            console.error('Error generating QR code:', error);
            showAlert('QR generation failed', 'danger');
        } finally {
            setLoadingState(submitBtn, false);
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
                <button class="btn btn-outline-primary btn-custom" onclick="qrGenerator.downloadQRCode('${ssid}')">
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
            showAlert('Enter your custom network details above', 'info');
        }
    }
}

export default QRGenerator;