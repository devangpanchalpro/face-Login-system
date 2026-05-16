"""
Face processing utilities.
Handles Base64 image decoding and face_recognition encoding.
"""
import base64
import cv2
import numpy as np
import face_recognition


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
    Extract a 128-dimensional face encoding from a Base64-encoded image.

    Returns:
        (encoding, message): encoding is a numpy array or None,
                             message is 'OK' or an error description.
    """
    try:
        img = decode_base64_image(base64_str)
    except ValueError as e:
        return None, str(e)

    # Convert BGR → RGB for face_recognition
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Optional: histogram equalization for better accuracy in poor lighting
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_channel, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_channel = clahe.apply(l_channel)
    lab = cv2.merge((l_channel, a, b))
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    # Detect face locations
    locations = face_recognition.face_locations(enhanced)

    if len(locations) == 0:
        return None, "No face detected. Please ensure your face is clearly visible."
    if len(locations) > 1:
        return None, "Multiple faces detected. Only one person should be in the frame."

    # Extract 128-d encoding
    encodings = face_recognition.face_encodings(enhanced, locations)
    if not encodings:
        return None, "Could not encode the face. Please try again."

    return encodings[0], "OK"
