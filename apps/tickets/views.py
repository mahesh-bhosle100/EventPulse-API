from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import TicketType
from .serializers import TicketTypeSerializer
from apps.users.permissions import IsOrganizer


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
        event = Event.objects.get(pk=self.kwargs['event_id'])
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
