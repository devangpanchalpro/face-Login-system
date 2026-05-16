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
    const SCAN_INTERVAL = 2000; // ms between scans

    // Start camera
    const started = await cam.start();
    if (!started) {
        statusText.textContent = 'Camera error. Please allow camera permission.';
        statusText.style.color = '#ef4444';
        scanSpinner.classList.add('d-none');
        return;
    }

    statusText.textContent = 'Camera ready. Scanning your face...';

    // Wait a moment for camera to stabilize then start scanning
    setTimeout(() => startScanning(), 1500);

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
                const resp = await fetch('/api/login/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image_base64: frame }),
                });

                const data = await resp.json();

                if (data.success) {
                    // Match found!
                    isScanning = false;
                    cam.stop();
                    showSuccess(data.user);
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
            showFailure();
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

    function showFailure() {
        webcamWrapper.style.display = 'none';
        scanSpinner.classList.add('d-none');
        statusText.textContent = '';
        document.getElementById('login-status').classList.add('d-none');

        loginFailed.classList.remove('d-none');
        loginFailed.classList.add('animate-slide-up');
        showToast('Face not recognized. Access denied.', 'danger');
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
});
