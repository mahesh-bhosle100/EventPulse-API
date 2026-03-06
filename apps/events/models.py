from django.db import models
from apps.users.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Event(models.Model):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'

    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PUBLISHED, 'Published'),
        (CANCELLED, 'Cancelled'),
        (COMPLETED, 'Completed'),
    ]

    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    banner_image = models.ImageField(upload_to='events/banners/', blank=True, null=True)
    venue = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    address = models.TextField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    total_capacity = models.PositiveIntegerField()
    is_free = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'events'
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['city']),
            models.Index(fields=['status']),
            models.Index(fields=['start_datetime']),
            models.Index(fields=['end_datetime']),
            models.Index(fields=['organizer']),
            models.Index(fields=['category']),
            models.Index(fields=['city', 'start_datetime']),
        ]

    def __str__(self):
        return self.title

    @property
    def available_seats(self):
        booked = self.bookings.filter(
            status__in=['confirmed', 'pending']
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
        return self.total_capacity - booked

    @property
    def is_sold_out(self):
        return self.available_seats <= 0


class EventReview(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'event_reviews'
        unique_together = ['event', 'user']
        indexes = [
            models.Index(fields=['event']),
            models.Index(fields=['rating']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.event.title} ({self.rating}/5)'
