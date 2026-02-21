// QR Scanner functionality for camera and gallery
class QRScanner {
    constructor() {
        this.video = null;
        this.canvas = null;
        this.canvasContext = null;
        this.stream = null;
        this.scanning = false;
        this.scanInterval = null;
    }

    // Initialize scanner
    init(videoElementId, canvasElementId) {
        this.video = document.getElementById(videoElementId);
        this.canvas = document.getElementById(canvasElementId);
        this.canvasContext = this.canvas.getContext('2d');
    }

    // Start camera scanning
    async startCameraScanning() {
        try {
            // Check if media devices are supported
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Camera not supported on this device');
            }

            // Request camera access with rear camera preference for mobile
            const constraints = {
                video: {
                    facingMode: { ideal: 'environment' }, // Rear camera
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                }
            };

            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.video.srcObject = this.stream;

            // Wait for video to be ready
            await new Promise((resolve, reject) => {
                this.video.onloadedmetadata = () => resolve();
                this.video.onerror = () => reject(new Error('Video load failed'));
                this.video.play();
            });

            this.scanning = true;
            this.scanForQR();

            return true;
        } catch (error) {
            console.error('Error accessing camera:', error);

            let errorMessage = 'Unable to access camera. ';

            if (error.name === 'NotAllowedError') {
                errorMessage += 'Camera permission denied. Please allow camera access and try again.';
            } else if (error.name === 'NotFoundError') {
                errorMessage += 'No camera found on this device.';
            } else if (error.name === 'NotSupportedError') {
                errorMessage += 'Camera not supported on this browser.';
            } else if (error.name === 'NotReadableError') {
                errorMessage += 'Camera is already in use by another application.';
            } else if (error.message.includes('HTTPS')) {
                errorMessage += 'Camera access requires HTTPS. Please use a secure connection.';
            } else {
                errorMessage += 'Please check your camera settings and try again.';
            }

            this.showError(errorMessage);
            return false;
        }
    }

    // Stop camera scanning
    stopCameraScanning() {
        this.scanning = false;
        if (this.scanInterval) {
            clearInterval(this.scanInterval);
            this.scanInterval = null;
        }
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        if (this.video) {
            this.video.srcObject = null;
        }
    }

    // Continuously scan for QR codes
    scanForQR() {
        if (!this.scanning) return;

        if (this.video.readyState === this.video.HAVE_ENOUGH_DATA) {
            this.canvas.width = this.video.videoWidth;
            this.canvas.height = this.video.videoHeight;
            this.canvasContext.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);

            const imageData = this.canvasContext.getImageData(0, 0, this.canvas.width, this.canvas.height);
            const code = jsQR(imageData.data, imageData.width, imageData.height);

            if (code) {
                this.handleQRCode(code.data);
                return; // Stop scanning after finding QR code
            }
        }

        // Continue scanning
        this.scanInterval = setTimeout(() => this.scanForQR(), 500);
    }

    // Handle QR code from gallery upload
    async scanFromGallery(file) {
        return new Promise((resolve, reject) => {
            // Validate file type
            if (!file.type.startsWith('image/')) {
                reject(new Error('Please select a valid image file'));
                return;
            }

            // Check file size (limit to 10MB)
            if (file.size > 10 * 1024 * 1024) {
                reject(new Error('Image file is too large. Please select an image under 10MB'));
                return;
            }

            const reader = new FileReader();
            reader.onload = (e) => {
                const img = new Image();
                img.onload = () => {
                    // Resize large images for better performance
                    const maxDimension = 1024;
                    let { width, height } = img;

                    if (width > maxDimension || height > maxDimension) {
                        if (width > height) {
                            height = (height * maxDimension) / width;
                            width = maxDimension;
                        } else {
                            width = (width * maxDimension) / height;
                            height = maxDimension;
                        }
                    }

                    this.canvas.width = width;
                    this.canvas.height = height;
                    this.canvasContext.drawImage(img, 0, 0, width, height);

                    const imageData = this.canvasContext.getImageData(0, 0, width, height);
                    const code = jsQR(imageData.data, imageData.width, imageData.height);

                    if (code) {
                        resolve(code.data);
                    } else {
                        reject(new Error('No QR code found in the selected image. Please try a clearer image or different angle.'));
                    }
                };
                img.onerror = () => reject(new Error('Failed to load image. Please try a different image file.'));
                img.src = e.target.result;
            };
            reader.onerror = () => reject(new Error('Failed to read file. Please try again.'));
            reader.readAsDataURL(file);
        });
    }

    // Handle detected QR code
    handleQRCode(qrData) {
        this.stopCameraScanning();

        // Fill the QR data textarea
        const qrTextarea = document.getElementById('qr_data');
        if (qrTextarea) {
            qrTextarea.value = qrData;
        }

        // Show success message
        this.showSuccess('QR code scanned successfully!');

        // Parse QR data to extract amount if present
        const parts = qrData.split('|');
        if (parts.length > 3) {
            const amountInput = document.getElementById('amount');
            if (amountInput && !amountInput.value) {
                amountInput.value = parts[3];
            }
        }
    }

    // Show error message
    showError(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        this.insertAlert(alertDiv);
    }

    // Show success message
    showSuccess(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show';
        alertDiv.innerHTML = `
            <i class="fas fa-check-circle me-2"></i>${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        this.insertAlert(alertDiv);
    }

    // Insert alert into DOM
    insertAlert(alertDiv) {
        const container = document.querySelector('.container-fluid');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }
}

// Global scanner instance
const qrScanner = new QRScanner();
