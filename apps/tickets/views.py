from rest_framework import generics
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.shortcuts import get_object_or_404
from .models import TicketType
from .serializers import TicketTypeSerializer
from apps.users.permissions import IsOrganizer


@method_decorator(cache_page(settings.CACHE_TTL), name='dispatch')
@method_decorator(vary_on_headers('Authorization'), name='dispatch')
class TicketTypeListCreateView(generics.ListCreateAPIView):
    """List ticket types for an event or create a new ticket type."""
    serializer_class = TicketTypeSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsOrganizer()]
        return [AllowAny()]

    def get_queryset(self):
        return TicketType.objects.filter(
            event_id=self.kwargs['event_id']
        ).select_related('event')

    def perform_create(self, serializer):
        from apps.events.models import Event
        event = get_object_or_404(Event, pk=self.kwargs['event_id'])
        if event.organizer != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only add tickets to your own events")
        serializer.save(event=event)


class TicketTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a ticket type."""
    queryset = TicketType.objects.all()
    serializer_class = TicketTypeSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsOrganizer()]
        return [AllowAny()]

    def perform_update(self, serializer):
        ticket = self.get_object()
        if ticket.event.organizer != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only edit tickets for your own events")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.event.organizer != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete tickets for your own events")
        instance.delete()
