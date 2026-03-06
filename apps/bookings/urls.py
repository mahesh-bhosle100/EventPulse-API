from django.urls import path
from .views import (
    BookingCreateView, PaymentVerifyView,
    MyBookingsView, BookingDetailView, CancelBookingView
)

urlpatterns = [
    path('', BookingCreateView.as_view(), name='booking_create'),
    path('verify-payment/', PaymentVerifyView.as_view(), name='verify_payment'),
    path('my/', MyBookingsView.as_view(), name='my_bookings'),
    path('<int:pk>/', BookingDetailView.as_view(), name='booking_detail'),
    path('<int:pk>/cancel/', CancelBookingView.as_view(), name='cancel_booking'),
]
