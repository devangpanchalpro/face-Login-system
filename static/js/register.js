/**
 * Registration page logic — single front-face capture.
 */
document.addEventListener('DOMContentLoaded', async () => {
    const cam = new WebcamManager();
    const btnCapture = document.getElementById('btn-capture');
    const btnRetake = document.getElementById('btn-retake');
    const btnRegister = document.getElementById('btn-register');
    const registerSpinner = document.getElementById('register-spinner');
    const registerIcon = document.getElementById('register-icon');
    const registerText = document.getElementById('register-text');
    const webcamWrapper = document.getElementById('webcam-wrapper');
    const capturedPreview = document.getElementById('captured-preview');
    const capturedImage = document.getElementById('captured-image');
    const statusEl = document.getElementById('webcam-status');

    let capturedFrame = null;

    // Start camera
    const started = await cam.start();
    if (started) {
        statusEl.innerHTML = '<i class="bi bi-camera-fill me-1"></i> Camera Ready';
        statusEl.style.color = '#22c55e';
    } else {
        statusEl.innerHTML = '<i class="bi bi-exclamation-triangle-fill me-1"></i> Camera Error';
        statusEl.style.color = '#ef4444';
        showToast('Could not access camera. Please allow camera permission.', 'danger');
    }

    // Capture front face
    btnCapture.addEventListener('click', () => {
        const frame = cam.captureFrame();
        if (!frame) {
            showToast('Camera not ready. Please wait.', 'warning');
            return;
        }

        capturedFrame = frame;
        capturedImage.src = frame;
        webcamWrapper.classList.add('d-none');
        capturedPreview.classList.remove('d-none');
        btnCapture.classList.add('d-none');
        btnRetake.classList.remove('d-none');
        btnRegister.disabled = false;

        cam.stop();
        showToast('Face captured! Ready to register.', 'success');
    });

    // Retake
    btnRetake.addEventListener('click', async () => {
        capturedFrame = null;
        webcamWrapper.classList.remove('d-none');
        capturedPreview.classList.add('d-none');
        btnCapture.classList.remove('d-none');
        btnRetake.classList.add('d-none');
        btnRegister.disabled = true;

        await cam.start();
        showToast('Retake — look straight at the camera.', 'info');
    });

    // Submit registration with single image
    btnRegister.addEventListener('click', async () => {
        const name = document.getElementById('reg-name').value.trim();
        const email = document.getElementById('reg-email').value.trim();
        const phone = document.getElementById('reg-phone').value.trim();
        const dob = document.getElementById('reg-dob').value;

        // Validation
        if (!name) { showToast('Please enter your name.', 'warning'); return; }
        if (!email) { showToast('Please enter your email.', 'warning'); return; }
        if (!capturedFrame) {
            showToast('Please capture your face first.', 'warning');
            return;
        }

        // Show loading
        btnRegister.disabled = true;
        registerSpinner.classList.remove('d-none');
        registerIcon.classList.add('d-none');
        registerText.textContent = 'Processing face...';

        try {
            const resp = await fetch('/api/register/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name, email, phone, dob,
                    image_base64: capturedFrame,
                }),
            });

            const data = await resp.json();

            if (data.success) {
                showToast(data.message, 'success');
                const targetUrl = data.redirect_to_dashboard ? '/dashboard/' : '/login/';
                setTimeout(() => window.location.href = targetUrl, 2000);
            } else {
                showToast(data.message, 'danger');
                btnRegister.disabled = false;
            }
        } catch (err) {
            showToast('Network error. Please try again.', 'danger');
            btnRegister.disabled = false;
        } finally {
            registerSpinner.classList.add('d-none');
            registerIcon.classList.remove('d-none');
            registerText.textContent = 'Register';
        }
    });
});
