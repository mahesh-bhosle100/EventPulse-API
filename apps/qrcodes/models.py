import uuid
from django.db import models
from apps.bookings.models import Booking
from apps.users.models import User


class QRCode(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='qrcode')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    qr_image = models.ImageField(upload_to='tickets/qrcodes/', blank=True, null=True)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    used_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'qrcodes'
        indexes = [
            models.Index(fields=['is_used']),
            models.Index(fields=['used_by']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'QR - {self.booking.booking_reference}'
