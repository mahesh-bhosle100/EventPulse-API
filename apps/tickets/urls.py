from django.urls import path
from .views import TicketTypeListCreateView, TicketTypeDetailView

urlpatterns = [
    path('event/<int:event_id>/', TicketTypeListCreateView.as_view(), name='ticket_type_list'),
    path('<int:pk>/', TicketTypeDetailView.as_view(), name='ticket_type_detail'),
]
