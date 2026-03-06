from rest_framework import serializers
from .models import Booking, Payment


class BookingCreateSerializer(serializers.Serializer):
    ticket_type_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, max_value=10)


class BookingSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_date = serializers.DateTimeField(source='event.start_datetime', read_only=True)
    ticket_name = serializers.CharField(source='ticket_type.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    payment_status = serializers.CharField(source='payment.status', read_only=True, default='N/A')

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_reference', 'user_email', 'event_title',
            'event_date', 'ticket_name', 'quantity', 'unit_price',
            'total_amount', 'status', 'ticket_pdf', 'attended',
            'payment_status', 'created_at'
        ]


class PaymentVerifySerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'razorpay_order_id', 'amount', 'currency', 'status', 'created_at']
