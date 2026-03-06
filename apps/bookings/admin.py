from django.contrib import admin
from .models import Booking, Payment


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_reference', 'user', 'event', 'quantity', 'total_amount', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['booking_reference', 'user__email', 'event__title']
    ordering = ['-created_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['booking', 'razorpay_order_id', 'amount', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['razorpay_order_id', 'booking__booking_reference']
