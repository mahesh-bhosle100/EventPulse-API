from rest_framework.permissions import BasePermission
from .models import User


class IsOrganizer(BasePermission):
    """Allow only organizers."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.ORGANIZER


class IsAttendee(BasePermission):
    """Allow only attendees."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.ATTENDEE


class IsOrganizerOrReadOnly(BasePermission):
    """Allow read-only for all, write for organizers."""
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_authenticated and request.user.role == User.ORGANIZER
