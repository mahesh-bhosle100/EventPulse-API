import razorpay
from razorpay.errors import BadRequestError, GatewayError, ServerError
import hmac as hmac_module
import hashlib
from django.conf import settings
from django.core.cache import cache
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Booking, Payment
from .serializers import (
    BookingCreateSerializer, BookingSerializer,
    PaymentVerifySerializer
)
from apps.tickets.models import TicketType
from apps.notifications.tasks import (
    generate_ticket_pdf_and_send_email,
    auto_cancel_unpaid_booking
)

razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


class BookingCreateView(APIView):
    """
    Create booking with Redis distributed lock to prevent double-booking.
    Initiates Razorpay payment order.
    """
    permission_classes = [IsAuthenticated]
    throttle_scope = 'payment'

    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ticket_type_id = serializer.validated_data['ticket_type_id']
        quantity = serializer.validated_data['quantity']

        try:
            ticket_type = TicketType.objects.select_related('event').get(pk=ticket_type_id)
        except TicketType.DoesNotExist:
            return Response({'error': 'Ticket type not found'}, status=status.HTTP_404_NOT_FOUND)

        if ticket_type.event.status != ticket_type.event.PUBLISHED:
            return Response({'error': 'Event is not available for booking'}, status=status.HTTP_400_BAD_REQUEST)

        if not ticket_type.is_available:
            return Response({'error': 'Tickets are not available for sale'}, status=status.HTTP_400_BAD_REQUEST)

        # Redis distributed lock to prevent double-booking
        # Prevents multiple users from booking the same last ticket simultaneously
        lock_key = f'ticket_lock:{ticket_type_id}'
        try:
            lock_acquired = cache.add(lock_key, request.user.id, timeout=30)
        except Exception:
            return Response(
                {'error': 'Booking service temporarily unavailable'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        if not lock_acquired:
            return Response(
                {'error': 'Someone else is booking this ticket. Please try again in a moment.'},
                status=status.HTTP_409_CONFLICT
            )

        try:
            # Re-check availability inside lock
            ticket_type.refresh_from_db()
            if ticket_type.available_quantity < quantity:
                return Response(
                    {'error': f'Only {ticket_type.available_quantity} tickets available'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            total_amount = ticket_type.price * quantity

            # Create Razorpay order
            if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
                return Response(
                    {'error': 'Payment gateway not configured'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            try:
                razorpay_order = razorpay_client.order.create({
                    'amount': int(total_amount * 100),  # Amount in paise
                    'currency': 'INR',
                    'payment_capture': 1
                })
            except (BadRequestError, GatewayError, ServerError) as exc:
                return Response(
                    {'error': 'Payment gateway error', 'detail': str(exc)},
                    status=status.HTTP_502_BAD_GATEWAY
                )

            # Create booking in PENDING state
            booking = Booking.objects.create(
                user=request.user,
                event=ticket_type.event,
                ticket_type=ticket_type,
                quantity=quantity,
                unit_price=ticket_type.price,
                total_amount=total_amount,
                status=Booking.PENDING
            )

            # Create payment record
            payment = Payment.objects.create(
                booking=booking,
                razorpay_order_id=razorpay_order['id'],
                amount=total_amount,
                currency='INR',
                status=Payment.INITIATED
            )

            # Schedule auto-cancel after 15 minutes if not paid
            auto_cancel_unpaid_booking.apply_async(
                args=[booking.id],
                countdown=900  # 15 minutes
            )

            return Response({
                'booking': BookingSerializer(booking).data,
                'payment': {
                    'razorpay_order_id': razorpay_order['id'],
                    'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                    'amount': int(total_amount * 100),
                    'currency': 'INR',
                    'booking_reference': booking.booking_reference
                }
            }, status=status.HTTP_201_CREATED)

        finally:
            # Always release lock (best effort)
            try:
                cache.delete(lock_key)
            except Exception:
                pass


class PaymentVerifyView(APIView):
    """
    Verify Razorpay payment signature and confirm booking.
    Triggers Celery task to generate PDF ticket and send email.
    """
    permission_classes = [IsAuthenticated]
    throttle_scope = 'payment'

    def post(self, request):
        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            return Response(
                {'error': 'Payment gateway not configured'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        razorpay_order_id = serializer.validated_data['razorpay_order_id']
        razorpay_payment_id = serializer.validated_data['razorpay_payment_id']
        razorpay_signature = serializer.validated_data['razorpay_signature']

        try:
            payment = Payment.objects.select_related('booking').get(
                razorpay_order_id=razorpay_order_id
            )
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)

        # Verify Razorpay signature
        generated_signature = hmac_module.new(
            key=settings.RAZORPAY_KEY_SECRET.encode(),
            msg=f'{razorpay_order_id}|{razorpay_payment_id}'.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

        if generated_signature != razorpay_signature:
            payment.status = Payment.FAILED
            payment.save()
            return Response({'error': 'Payment verification failed'}, status=status.HTTP_400_BAD_REQUEST)

        if payment.status == Payment.SUCCESS:
            return Response({
                'message': 'Payment already verified',
                'booking': BookingSerializer(payment.booking).data
            })

        # Update payment and booking
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = Payment.SUCCESS
        payment.save()

        booking = payment.booking
        booking.status = Booking.CONFIRMED
        booking.save()

        # Trigger Celery task: generate PDF and send email
        generate_ticket_pdf_and_send_email.delay(booking.id)

        return Response({
            'message': 'Payment successful! Your ticket will be emailed shortly.',
            'booking': BookingSerializer(booking).data
        })


class MyBookingsView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user
        ).select_related('event', 'ticket_type', 'payment')


class BookingDetailView(generics.RetrieveAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)


class CancelBookingView(APIView):
    """Cancel booking and initiate Razorpay refund."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            booking = Booking.objects.select_related('payment').get(
                pk=pk, user=request.user
            )
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

        if booking.status == Booking.CANCELLED:
            return Response({'error': 'Booking is already cancelled'}, status=status.HTTP_400_BAD_REQUEST)

        if booking.status != Booking.CONFIRMED:
            booking.status = Booking.CANCELLED
            booking.save()
            return Response({'message': 'Booking cancelled'})

        # Initiate refund via Razorpay
        try:
            razorpay_client.payment.refund(
                booking.payment.razorpay_payment_id,
                {'amount': int(booking.total_amount * 100)}
            )
            booking.status = Booking.REFUNDED
            booking.payment.status = Payment.REFUNDED
            booking.payment.save()
        except Exception:
            booking.status = Booking.CANCELLED

        booking.save()

        return Response({
            'message': 'Booking cancelled and refund initiated',
            'booking': BookingSerializer(booking).data
        })
