from django.contrib import admin
from django.utils.html import format_html
from .models import FaceUser, FaceEncoding, LoginHistory


@admin.register(FaceUser)
class FaceUserAdmin(admin.ModelAdmin):
    list_display = ('photo_preview', 'name', 'email', 'phone', 'encoding_count', 'last_login', 'login_count', 'created_at')
    list_filter = ('created_at', 'last_login')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('encoding_preview', 'created_at', 'last_login', 'login_count', 'encoding_count', 'photo_full')
    exclude = ('face_encoding',)  # Exclude raw vector — shown via encoding_preview instead

    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="40" height="40" style="border-radius:50%; object-fit:cover;" />', obj.photo.url)
        return '—'
    photo_preview.short_description = 'Photo'

    def photo_full(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="200" style="border-radius:12px;" />', obj.photo.url)
        return 'No photo uploaded'
    photo_full.short_description = 'Face Photo'

    def encoding_preview(self, obj):
        if obj.face_encoding is not None:
            vec = list(obj.face_encoding)[:5]
            return f"128-d vector: [{', '.join(f'{v:.4f}' for v in vec)}, ...]"
        return 'No encoding'
    encoding_preview.short_description = 'Face Encoding (preview)'


@admin.register(FaceEncoding)
class FaceEncodingAdmin(admin.ModelAdmin):
    list_display = ('user', 'label', 'created_at')
    list_filter = ('label', 'created_at')
    search_fields = ('user__name', 'user__email')
    readonly_fields = ('encoding_preview', 'created_at')
    exclude = ('encoding',)  # Exclude raw vector — shown via encoding_preview instead

    def encoding_preview(self, obj):
        if obj.encoding is not None:
            vec = list(obj.encoding)[:5]
            return f"128-d vector: [{', '.join(f'{v:.4f}' for v in vec)}, ...]"
        return 'No encoding'
    encoding_preview.short_description = 'Encoding (preview)'


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'logged_in_at', 'confidence', 'ip_address')
    list_filter = ('logged_in_at',)
    search_fields = ('user__name', 'user__email', 'ip_address')
    readonly_fields = ('logged_in_at',)
