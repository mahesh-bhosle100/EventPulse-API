from django.contrib import admin
from .models import Event, Category, EventReview


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'organizer', 'city', 'start_datetime', 'status', 'total_capacity']
    list_filter = ['status', 'city', 'is_free']
    search_fields = ['title', 'venue', 'city']
    ordering = ['-start_datetime']


@admin.register(EventReview)
class EventReviewAdmin(admin.ModelAdmin):
    list_display = ['event', 'user', 'rating', 'created_at']
