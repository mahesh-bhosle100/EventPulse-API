from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Event, Category, EventReview
from .serializers import (
    EventListSerializer, EventDetailSerializer,
    CategorySerializer, EventReviewSerializer
)
from .filters import EventFilter
from apps.users.permissions import IsOrganizer


class CategoryListView(generics.ListCreateAPIView):
    """List categories or create a new category."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class EventListCreateView(generics.ListCreateAPIView):
    """List events or create a new event."""
    queryset = Event.objects.select_related('organizer', 'category').filter(status=Event.PUBLISHED)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EventFilter
    search_fields = ['title', 'venue', 'city']
    ordering_fields = ['start_datetime', 'created_at']
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EventDetailSerializer
        return EventListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsOrganizer()]
        return [AllowAny()]

    def get_queryset(self):
        # Organizers can see their own draft events
        if self.request.user.is_authenticated and self.request.user.is_organizer:
            return Event.objects.filter(organizer=self.request.user).select_related('organizer', 'category')
        return Event.objects.filter(status=Event.PUBLISHED).select_related('organizer', 'category')

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)


class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an event."""
    queryset = Event.objects.select_related('organizer', 'category')
    serializer_class = EventDetailSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsOrganizer()]
        return [AllowAny()]

    def perform_update(self, serializer):
        event = self.get_object()
        if event.organizer != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only edit your own events")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.organizer != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own events")
        instance.delete()


class EventReviewListCreateView(generics.ListCreateAPIView):
    """List or create reviews for a specific event."""
    serializer_class = EventReviewSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        return EventReview.objects.filter(
            event_id=self.kwargs['event_id']
        ).select_related('user')

    def perform_create(self, serializer):
        event = Event.objects.get(pk=self.kwargs['event_id'])
        try:
            serializer.save(user=self.request.user, event=event)
        except Exception as exc:
            from django.db import IntegrityError
            if isinstance(exc, IntegrityError):
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'detail': 'You have already reviewed this event'})
            raise
