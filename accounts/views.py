"""
Views for face-based registration, login, and dashboard.
Uses PostgreSQL + pgvector for fast vector similarity search.
"""
import json
import base64
import uuid
import time
import numpy as np

from django.core.files.base import ContentFile

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone

from .models import FaceUser, FaceEncoding, LoginHistory
from .face_utils import get_face_encoding
from .vector_search import search_face


def get_client_ip(request):
    """Extract client IP from request headers (supports proxies)."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ──────────────────────────────────────
#  Page Views (render HTML templates)
# ──────────────────────────────────────

def home_page(request):
    """Landing page."""
    total_users = FaceUser.objects.count()
    return render(request, 'home.html', {'total_users': total_users})


def register_page(request):
    """Registration form with webcam."""
    return render(request, 'register.html')


def login_page(request):
    """Login page with webcam auto-scan."""
    return render(request, 'login.html')


def dashboard_page(request):
    """
    Dashboard showing logged-in user details + login history.
    Requires user_id in session (set by api_login).
    """
    user_id = request.session.get('face_user_id')
    if not user_id:
        return redirect('login_page')

    try:
        user = FaceUser.objects.get(id=user_id)
    except FaceUser.DoesNotExist:
        request.session.flush()
        return redirect('login_page')

    # Get recent login history (last 10 entries)
    history = LoginHistory.objects.filter(user=user)[:10]

    context = {
        'user': user,
        'history': history,
    }
    return render(request, 'dashboard.html', context)


def logout_view(request):
    """Clear session and redirect to home."""
    request.session.flush()
    return redirect('home_page')


# ──────────────────────────────────────
#  API Views (JSON endpoints)
# ──────────────────────────────────────

@csrf_exempt
@require_POST
def api_register(request):
    """
    Register a new user with a single front-face encoding.

    Expects JSON body:
    {
        "name": "...",
        "email": "...",
        "phone": "...",
        "dob": "YYYY-MM-DD",
        "image_base64": "data:image/jpeg;base64,..."
    }
    """
    start_time = time.time()
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)

    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    dob = data.get('dob', '').strip()
    image_base64 = data.get('image_base64', '')

    # Validation
    if not name:
        return JsonResponse({'success': False, 'message': 'Name is required.'}, status=400)
    if not email:
        return JsonResponse({'success': False, 'message': 'Email is required.'}, status=400)
    if not image_base64:
        return JsonResponse({'success': False, 'message': 'Face image is required.'}, status=400)

    # Check if email already registered
    if FaceUser.objects.filter(email=email).exists():
        return JsonResponse({'success': False, 'message': 'This email is already registered.'}, status=400)

    # Extract face encoding from the captured image
    encoding, msg = get_face_encoding(image_base64)
    if encoding is None:
        return JsonResponse({'success': False, 'message': msg}, status=400)

    # Check if face is already registered (Auto-Login feature)
    matched_user, distance = search_face(encoding, threshold=0.45)
    if matched_user:
        import face_recognition

        # Get all encodings for this user from pgvector
        user_encodings = []
        face_enc_records = FaceEncoding.objects.filter(user=matched_user)

        for fe in face_enc_records:
            stored_enc = np.array(fe.encoding)
            user_encodings.append(stored_enc)

        if not user_encodings:
            # Fallback to primary encoding
            stored_enc = np.array(matched_user.face_encoding)
            user_encodings.append(stored_enc)

        # Compare against ALL encodings — if ANY match, approve auto-login
        matches = face_recognition.compare_faces(
            user_encodings, encoding, tolerance=0.4
        )
        if any(matches):
            previous_login = matched_user.last_login
            matched_user.record_login()

            # Record login duration
            duration = time.time() - start_time
            LoginHistory.objects.create(
                user=matched_user,
                confidence=distance,
                ip_address=get_client_ip(request),
                login_duration=round(duration, 3)
            )

            # Store user ID in session
            request.session['face_user_id'] = matched_user.id

            return JsonResponse({
                'success': True,
                'message': f'Face already registered! Logging you in as {matched_user.name}...',
                'redirect_to_dashboard': True,
                'user': {
                    'id': matched_user.id,
                    'name': matched_user.name,
                    'email': matched_user.email,
                    'phone': matched_user.phone or '',
                    'dob': str(matched_user.dob) if matched_user.dob else '',
                    'last_login': previous_login.strftime('%d %b %Y, %I:%M %p') if previous_login else 'First login!',
                    'login_count': matched_user.login_count,
                    'confidence': round(distance, 4),
                    'login_duration': round(duration, 3)
                }
            })

    # Store as list for pgvector VectorField
    encoding_list = encoding.tolist()

    # Parse date of birth
    dob_parsed = None
    if dob:
        try:
            from datetime import datetime
            dob_parsed = datetime.strptime(dob, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    # Create user with front-face encoding
    user = FaceUser.objects.create(
        name=name,
        email=email,
        phone=phone or None,
        dob=dob_parsed,
        face_encoding=encoding_list,
        encoding_count=1,
    )

    # Store encoding in FaceEncoding table (with HNSW index for fast search)
    FaceEncoding.objects.create(
        user=user,
        encoding=encoding_list,
        label='front',
    )

    # Save captured face photo
    try:
        img_data = image_base64.split(',', 1)[1] if ',' in image_base64 else image_base64
        img_bytes = base64.b64decode(img_data)
        filename = f"face_{user.id}_{uuid.uuid4().hex[:8]}.jpg"
        user.photo.save(filename, ContentFile(img_bytes), save=True)
    except Exception:
        pass  # Photo is optional, don't fail registration

    return JsonResponse({
        'success': True,
        'message': f'User "{name}" registered successfully!',
        'user_id': user.id,
    })


@csrf_exempt
@require_POST
def api_login(request):
    """
    Authenticate a user by face match using pgvector nearest-neighbor search.

    Expects JSON body:
    {
        "image_base64": "data:image/jpeg;base64,..."
    }

    Returns matched user data + last_login info on success.
    """
    start_time = time.time()
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)

    client_dur = data.get('client_duration')

    image_base64 = data.get('image_base64', '')
    if not image_base64:
        return JsonResponse({'success': False, 'message': 'Face image is required.'}, status=400)

    # Extract face encoding from the captured image
    encoding, msg = get_face_encoding(image_base64)
    if encoding is None:
        return JsonResponse({'success': False, 'message': msg}, status=400)

    # Search using pgvector (PostgreSQL native vector similarity search)
    # Threshold 0.45 = strict match (~98%+ accuracy), safe for 5M+ users
    matched_user, distance = search_face(encoding, threshold=0.45)

    if matched_user:
        # Save previous last_login for "last seen" display
        previous_login = matched_user.last_login

        # Update last_login + increment login_count
        matched_user.record_login()

        # Get client_duration if provided, otherwise fallback to server processing time
        duration = data.get('client_duration')
        if duration is None:
            duration = time.time() - start_time
        else:
            try:
                duration = float(duration)
            except (ValueError, TypeError):
                duration = time.time() - start_time

        # Create audit trail entry
        LoginHistory.objects.create(
            user=matched_user,
            confidence=distance,
            ip_address=get_client_ip(request),
            login_duration=round(duration, 3),
        )

        # Store user ID in session for dashboard access
        request.session['face_user_id'] = matched_user.id

        return JsonResponse({
            'success': True,
            'message': 'Login successful!',
            'user': {
                'id': matched_user.id,
                'name': matched_user.name,
                'email': matched_user.email,
                'phone': matched_user.phone or '',
                'dob': str(matched_user.dob) if matched_user.dob else '',
                'last_login': previous_login.strftime('%d %b %Y, %I:%M %p') if previous_login else 'First login!',
                'login_count': matched_user.login_count,
                'confidence': round(distance, 4),
                'login_duration': round(duration, 3),
                'encodings_stored': matched_user.encoding_count,
            }
        })

    return JsonResponse({
        'success': False,
        'message': 'Face not recognized. Please register first.',
        'redirect_to_register': True,
        'distance': round(distance, 4),
    })


@require_GET
def api_login_history(request, user_id):
    """
    Get paginated login history for a user.
    Returns the last 20 login entries.
    """
    try:
        user = FaceUser.objects.get(id=user_id)
    except FaceUser.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found.'}, status=404)

    history = LoginHistory.objects.filter(user=user)[:20]
    entries = [
        {
            'logged_in_at': entry.logged_in_at.strftime('%d %b %Y, %I:%M %p'),
            'confidence': round(entry.confidence, 4),
            'ip_address': entry.ip_address or 'N/A',
        }
        for entry in history
    ]

    return JsonResponse({
        'success': True,
        'user_name': user.name,
        'total_logins': user.login_count,
        'history': entries,
    })
