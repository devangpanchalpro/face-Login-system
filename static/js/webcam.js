/**
 * Webcam utility module.
 * Handles getUserMedia, canvas capture, and Base64 extraction.
 */

class WebcamManager {
    constructor(videoId = 'webcam', canvasId = 'webcam-canvas') {
        this.video = document.getElementById(videoId);
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
        this.stream = null;
        this.isReady = false;
    }

    /**
     * Start the webcam stream.
     * @returns {Promise<boolean>} true if camera started successfully.
     */
    async start() {
        // Check if mediaDevices API is available (requires HTTPS)
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            console.error('getUserMedia not available. Page must be served over HTTPS.');
            this.isReady = false;
            return false;
        }

        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user',
                },
                audio: false,
            });
            this.video.srcObject = this.stream;
            await this.video.play();
            this.isReady = true;
            return true;
        } catch (err) {
            console.error('Webcam error:', err.name, err.message);
            this.isReady = false;
            return false;
        }
    }

    /**
     * Capture the current frame as a Base64 JPEG string.
     * @returns {string|null} Base64 data URL or null if not ready.
     */
    captureFrame() {
        if (!this.isReady || !this.video.videoWidth) return null;

        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        this.ctx.drawImage(this.video, 0, 0);
        return this.canvas.toDataURL('image/jpeg', 0.9);
    }

    /**
     * Stop the webcam stream and release resources.
     */
    stop() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        this.isReady = false;
    }
}

// Export globally
window.WebcamManager = WebcamManager;
