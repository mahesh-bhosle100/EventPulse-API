from django.contrib import admin
from .models import QRCode


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ['booking', 'token', 'is_used', 'used_at', 'created_at']
    list_filter = ['is_used']
    search_fields = ['booking__booking_reference']
    readonly_fields = ['token', 'created_at']
