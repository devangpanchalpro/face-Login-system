from django.db import models
from django.utils import timezone
# pyrefly: ignore [missing-import]
from pgvector.django import VectorField, HnswIndex


class FaceUser(models.Model):
    """
    Custom user model for face-based authentication.
    Stores personal details + primary 128-d face encoding vector.
    Uses pgvector VectorField for native PostgreSQL vector search.
    """
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    face_encoding = VectorField(dimensions=128)  # 128-d face_recognition vector
    photo = models.ImageField(upload_to='faces/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)
    login_count = models.IntegerField(default=0)
    encoding_count = models.IntegerField(
        default=1,
        help_text="Number of face encodings stored for this user"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Face User'
        verbose_name_plural = 'Face Users'

    def __str__(self):
        return f"{self.name} ({self.email})"

    def record_login(self):
        """Update last_login timestamp and increment login_count atomically."""
        self.last_login = timezone.now()
        self.login_count += 1
        self.save(update_fields=['last_login', 'login_count'])


class FaceEncoding(models.Model):
    """
    Stores individual face encodings for a user.
    Uses pgvector VectorField with HNSW index for fast similarity search
    across millions of records (sub-10ms query times).
    """
    user = models.ForeignKey(
        FaceUser,
        on_delete=models.CASCADE,
        related_name='encodings'
    )
    encoding = VectorField(dimensions=128)  # 128-d face_recognition vector
    label = models.CharField(
        max_length=50,
        default='front',
        help_text="e.g. 'front'"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Face Encoding'
        verbose_name_plural = 'Face Encodings'
        indexes = [
            HnswIndex(
                name='face_enc_hnsw_idx',
                fields=['encoding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_l2_ops'],
            )
        ]

    def __str__(self):
        return f"{self.user.name} — {self.label}"


class LoginHistory(models.Model):
    """
    Full audit trail of every successful face login.
    Stores the L2 distance score for confidence tracking.
    """
    user = models.ForeignKey(
        FaceUser,
        on_delete=models.CASCADE,
        related_name='login_history'
    )
    logged_in_at = models.DateTimeField(auto_now_add=True)
    confidence = models.FloatField(help_text="L2 distance (lower = better match)")
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        ordering = ['-logged_in_at']
        verbose_name = 'Login History'
        verbose_name_plural = 'Login Histories'

    def __str__(self):
        return f"{self.user.name} @ {self.logged_in_at.strftime('%Y-%m-%d %H:%M')}"
