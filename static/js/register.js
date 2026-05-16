/**
 * Registration page logic.
 * Manages form + webcam capture + API submission.
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

    let capturedBase64 = null;

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

    // Capture face
    btnCapture.addEventListener('click', () => {
        const frame = cam.captureFrame();
        if (!frame) {
            showToast('Camera not ready. Please wait.', 'warning');
            return;
        }

        capturedBase64 = frame;
        capturedImage.src = frame;

        // Show preview, hide webcam
        webcamWrapper.classList.add('d-none');
        capturedPreview.classList.remove('d-none');
        btnCapture.classList.add('d-none');
        btnRetake.classList.remove('d-none');
        btnRegister.disabled = false;

        cam.stop();
        showToast('Face captured successfully!', 'success');
    });

    // Retake
    btnRetake.addEventListener('click', async () => {
        capturedBase64 = null;
        webcamWrapper.classList.remove('d-none');
        capturedPreview.classList.add('d-none');
        btnCapture.classList.remove('d-none');
        btnRetake.classList.add('d-none');
        btnRegister.disabled = true;

        await cam.start();
        statusEl.innerHTML = '<i class="bi bi-camera-fill me-1"></i> Camera Ready';
    });

    // Submit registration
    btnRegister.addEventListener('click', async () => {
        const name = document.getElementById('reg-name').value.trim();
        const email = document.getElementById('reg-email').value.trim();
        const phone = document.getElementById('reg-phone').value.trim();
        const dob = document.getElementById('reg-dob').value;

        // Validation
        if (!name) { showToast('Please enter your name.', 'warning'); return; }
        if (!email) { showToast('Please enter your email.', 'warning'); return; }
        if (!capturedBase64) { showToast('Please capture your face first.', 'warning'); return; }

        // Show loading
        btnRegister.disabled = true;
        registerSpinner.classList.remove('d-none');
        registerIcon.classList.add('d-none');
        registerText.textContent = 'Processing...';

        try {
            const resp = await fetch('/api/register/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name, email, phone, dob,
                    image_base64: capturedBase64,
                }),
            });

            const data = await resp.json();

            if (data.success) {
                showToast(data.message, 'success');
                setTimeout(() => window.location.href = '/login/', 2000);
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
