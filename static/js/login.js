/**
 * Login page logic.
 * Auto-captures frames from webcam and sends to API for face matching.
 */
document.addEventListener('DOMContentLoaded', async () => {
    const cam = new WebcamManager();
    const statusText = document.getElementById('status-text');
    const scanSpinner = document.getElementById('scan-spinner');
    const loginResult = document.getElementById('login-result');
    const loginFailed = document.getElementById('login-failed');
    const webcamWrapper = document.getElementById('webcam-wrapper');

    let isScanning = false;
    let attempts = 0;
    const MAX_ATTEMPTS = 15;
    const SCAN_INTERVAL = 800; // ms between scans (optimized for speed)

    let cameraStartTime = null;

    // Start camera
    const started = await cam.start();
    if (!started) {
        statusText.textContent = 'Camera error. Please allow camera permission.';
        statusText.style.color = '#ef4444';
        scanSpinner.classList.add('d-none');
        return;
    }

    cameraStartTime = Date.now();
    statusText.textContent = 'Camera ready. Scanning your face...';

    // Wait a moment for camera to stabilize then start scanning
    setTimeout(() => startScanning(), 500);

    async function startScanning() {
        isScanning = true;
        statusText.textContent = 'Scanning for face match...';

        while (isScanning && attempts < MAX_ATTEMPTS) {
            const frame = cam.captureFrame();
            if (!frame) {
                await sleep(500);
                continue;
            }

            statusText.textContent = `Scanning... (attempt ${attempts + 1}/${MAX_ATTEMPTS})`;

            try {
                const clientDuration = (Date.now() - cameraStartTime) / 1000;
                const resp = await fetch('/api/login/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        image_base64: frame,
                        client_duration: clientDuration,
                        camera_start_time: cameraStartTime,
                        current_time: Date.now()
                    }),
                });

                const data = await resp.json();

                if (data.success) {
                    // Match found!
                    isScanning = false;
                    cam.stop();
                    showSuccess(data.user);
                    return;
                }

                // Face detected but not matched — check if we should redirect
                if (data.redirect_to_register && attempts >= 3) {
                    // After 3 failed attempts with redirect flag, stop early
                    isScanning = false;
                    cam.stop();
                    showFailureWithRedirect();
                    return;
                }
            } catch (err) {
                console.error('Scan error:', err);
            }

            attempts++;
            if (isScanning) await sleep(SCAN_INTERVAL);
        }

        // All attempts exhausted
        if (isScanning) {
            isScanning = false;
            cam.stop();
            showFailureWithRedirect();
        }
    }

    function showSuccess(user) {
        // Hide scanner
        webcamWrapper.style.display = 'none';
        scanSpinner.classList.add('d-none');
        statusText.textContent = '';
        document.getElementById('login-status').classList.add('d-none');

        // Show result
        document.getElementById('result-name').textContent = user.name;
        document.getElementById('result-email').textContent = user.email;
        document.getElementById('result-last-login').innerHTML =
            `<i class="bi bi-clock me-1"></i> Last: ${user.last_login}`;
        document.getElementById('result-login-count').innerHTML =
            `<i class="bi bi-graph-up me-1"></i> Logins: ${user.login_count}`;

        loginResult.classList.remove('d-none');
        loginResult.classList.add('animate-slide-up');
        showToast(`Welcome back, ${user.name}!`, 'success');
    }

    function showFailureWithRedirect() {
        webcamWrapper.style.display = 'none';
        scanSpinner.classList.add('d-none');
        statusText.textContent = '';
        document.getElementById('login-status').classList.add('d-none');

        loginFailed.classList.remove('d-none');
        loginFailed.classList.add('animate-slide-up');

        // Add redirect button and countdown
        const failedMsg = loginFailed.querySelector('.result-card') || loginFailed;
        if (!document.getElementById('register-redirect-btn')) {
            const redirectDiv = document.createElement('div');
            redirectDiv.className = 'text-center mt-3';
            redirectDiv.innerHTML = `
                <p class="text-secondary mb-2">Face not recognized. You need to register first!</p>
                <a href="/register/" id="register-redirect-btn" class="btn btn-glow px-4">
                    <i class="bi bi-person-plus-fill me-2"></i>Register Now
                </a>
                <p class="text-secondary mt-3 mb-0" id="redirect-countdown">
                    Redirecting to Register in <span id="countdown-num">5</span>s...
                </p>
            `;
            failedMsg.appendChild(redirectDiv);

            // Auto-redirect countdown
            let seconds = 5;
            const countdownEl = document.getElementById('countdown-num');
            const timer = setInterval(() => {
                seconds--;
                if (countdownEl) countdownEl.textContent = seconds;
                if (seconds <= 0) {
                    clearInterval(timer);
                    window.location.href = '/register/';
                }
            }, 1000);
        }

        showToast('Face not recognized. Redirecting to registration...', 'warning');
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
});

