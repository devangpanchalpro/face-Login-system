/**
 * Webcam utility module.
 * Handles getUserMedia, canvas capture, face detection, and Base64 extraction.
 */

class WebcamManager {
    constructor(videoId = 'webcam', canvasId = 'webcam-canvas') {
        this.video = document.getElementById(videoId);
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
        this.stream = null;
        this.isReady = false;
        this._detectLoop = null;

        // Initialize browser FaceDetector if available (Chrome/Edge)
        this.faceDetector = null;
        if (window.FaceDetector) {
            this.faceDetector = new FaceDetector({ fastMode: true, maxDetectedFaces: 5 });
        }
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
                    width: { ideal: 320 },
                    height: { ideal: 240 },
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
        return this.canvas.toDataURL('image/jpeg', 0.6);
    }

    /**
     * Detect faces in the current video frame using browser FaceDetector API.
     * @returns {Promise<number>} Number of faces detected (0, 1, 2+), or -1 if unsupported.
     */
    async detectFaces() {
        if (!this.faceDetector || !this.isReady || !this.video.videoWidth) {
            return -1; // API not available
        }
        try {
            const faces = await this.faceDetector.detect(this.video);
            return faces.length;
        } catch (err) {
            return -1;
        }
    }

    /**
     * Start continuous face detection loop.
     * Calls the callback every ~300ms with the number of detected faces.
     * @param {function(number)} callback - receives face count (0, 1, 2+, or -1 if unsupported)
     * @param {number} intervalMs - detection interval in milliseconds
     */
    startFaceDetection(callback, intervalMs = 300) {
        this.stopFaceDetection();
        this._detectLoop = setInterval(async () => {
            if (!this.isReady) return;
            const count = await this.detectFaces();
            callback(count);
        }, intervalMs);
    }

    /**
     * Stop the continuous face detection loop.
     */
    stopFaceDetection() {
        if (this._detectLoop) {
            clearInterval(this._detectLoop);
            this._detectLoop = null;
        }
    }

    /**
     * Stop the webcam stream and release resources.
     */
    stop() {
        this.stopFaceDetection();
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        this.isReady = false;
    }
}

// Export globally
window.WebcamManager = WebcamManager;
