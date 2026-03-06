from django.urls import path
from .views import GetQRCodeView, ValidateCheckinView

urlpatterns = [
    path('booking/<int:booking_id>/qr/', GetQRCodeView.as_view(), name='get_qr_code'),
    path('validate/', ValidateCheckinView.as_view(), name='validate_checkin'),
]
