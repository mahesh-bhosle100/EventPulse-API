from django.contrib import admin
from .models import TicketType


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'event', 'ticket_type', 'price', 'total_quantity', 'is_active']
    list_filter = ['ticket_type', 'is_active']
    search_fields = ['name', 'event__title']
