from django.utils import timezone
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import QRCode
from apps.bookings.models import Booking
from apps.users.permissions import IsOrganizer


class GetQRCodeView(APIView):
    """Return the QR code image URL for a confirmed booking."""
    permission_classes = [IsAuthenticated]

    def get(self, request, booking_id):
        try:
            booking = Booking.objects.select_related('qrcode').get(
                pk=booking_id, user=request.user
            )
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

        if booking.status != Booking.CONFIRMED:
            return Response({'error': 'QR code only available for confirmed bookings'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            qr = booking.qrcode
        except QRCode.DoesNotExist:
            return Response({'error': 'QR code not generated yet'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'booking_reference': booking.booking_reference,
            'qr_token': str(qr.token),
            'qr_image_url': request.build_absolute_uri(qr.qr_image.url) if qr.qr_image else None,
            'is_used': qr.is_used,
        })


class ValidateCheckinView(APIView):
    """
    Organizer scans QR code at event entry.
    Uses Redis cache to prevent duplicate scan in race conditions.
    """
    permission_classes = [IsOrganizer]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'QR token is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Redis lock to prevent double scan
        lock_key = f'checkin_lock:{token}'
        lock_acquired = cache.add(lock_key, 1, timeout=10)

        if not lock_acquired:
            return Response({'error': 'Scan in progress, please wait'}, status=status.HTTP_409_CONFLICT)

        try:
            qr = QRCode.objects.select_related(
                'booking__event', 'booking__user', 'booking__ticket_type'
            ).get(token=token)
        except QRCode.DoesNotExist:
            cache.delete(lock_key)
            return Response({'error': 'Invalid QR code'}, status=status.HTTP_404_NOT_FOUND)

        if qr.is_used:
            cache.delete(lock_key)
            return Response({
                'error': 'Ticket already used',
                'used_at': qr.used_at,
            }, status=status.HTTP_400_BAD_REQUEST)

        if qr.booking.status != Booking.CONFIRMED:
            cache.delete(lock_key)
            return Response({'error': 'Booking is not confirmed'}, status=status.HTTP_400_BAD_REQUEST)

        # Mark ticket as used
        qr.is_used = True
        qr.used_at = timezone.now()
        qr.used_by = request.user
        qr.save()

        qr.booking.attended = True
        qr.booking.save()

        cache.delete(lock_key)

        return Response({
            'message': 'Check-in successful',
            'attendee': qr.booking.user.full_name,
            'event': qr.booking.event.title,
            'ticket_type': qr.booking.ticket_type.name,
            'quantity': qr.booking.quantity,
        })
