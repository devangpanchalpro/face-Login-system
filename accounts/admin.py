from django.contrib import admin
from django.utils.html import format_html
from .models import FaceUser, LoginHistory


@admin.register(FaceUser)
class FaceUserAdmin(admin.ModelAdmin):
    list_display = ('photo_preview', 'name', 'email', 'phone', 'last_login', 'login_count', 'created_at')
    list_filter = ('created_at', 'last_login')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('face_encoding', 'created_at', 'last_login', 'login_count', 'photo_full')

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


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'logged_in_at', 'confidence', 'ip_address')
    list_filter = ('logged_in_at',)
    search_fields = ('user__name', 'user__email', 'ip_address')
    readonly_fields = ('logged_in_at',)
