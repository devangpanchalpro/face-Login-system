"""
Face processing utilities — powered by InsightFace (ArcFace + SCRFD).
Ultra-fast detection (~5ms) and 512-d embedding extraction (~10ms).
"""
import base64
import cv2
import numpy as np
from insightface.app import FaceAnalysis

# Initialize InsightFace model once at module load (singleton pattern)
# buffalo_l = SCRFD detector + ArcFace recognizer
_face_app = None


def _get_face_app():
    """Lazy-load the InsightFace model (loaded once, reused forever)."""
    global _face_app
    if _face_app is None:
        _face_app = FaceAnalysis(
            name='buffalo_l',
            providers=['CPUExecutionProvider']
        )
        # det_size=(320, 320) = optimal speed/accuracy tradeoff
        _face_app.prepare(ctx_id=0, det_size=(320, 320))
    return _face_app


def decode_base64_image(base64_str):
    """
    Convert a Base64-encoded image string to a numpy array (BGR format).
    Handles the 'data:image/...;base64,' prefix from browser canvas.
    """
    # Strip the data URL header if present
    if ',' in base64_str:
        base64_str = base64_str.split(',', 1)[1]

    img_bytes = base64.b64decode(base64_str)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Could not decode the image. Invalid Base64 data.")

    return img


def get_face_encoding(base64_str):
    """
    Extract a 512-dimensional face encoding from a Base64-encoded image
    using InsightFace (ArcFace model).

    Returns:
        (encoding, message): encoding is a numpy array (512-d) or None,
                             message is 'OK' or an error description.
    """
    try:
        img = decode_base64_image(base64_str)
    except ValueError as e:
        return None, str(e)

    # Resize if too large for faster processing
    h, w = img.shape[:2]
    max_dim = 640
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    # Run InsightFace detection + embedding extraction in one call
    app = _get_face_app()
    faces = app.get(img)

    if len(faces) == 0:
        return None, "No face detected. Please ensure your face is clearly visible."
    if len(faces) > 1:
        return None, "Multiple faces detected. Only one person should be in the frame."

    # Get the normalized 512-d embedding
    embedding = faces[0].normed_embedding

    if embedding is None:
        return None, "Could not encode the face. Please try again."

    return embedding, "OK"
