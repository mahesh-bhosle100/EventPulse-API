from django.db import models
from apps.events.models import Event


class TicketType(models.Model):
    GENERAL = 'general'
    VIP = 'vip'
    EARLY_BIRD = 'early_bird'
    STUDENT = 'student'

    TYPE_CHOICES = [
        (GENERAL, 'General'),
        (VIP, 'VIP'),
        (EARLY_BIRD, 'Early Bird'),
        (STUDENT, 'Student'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_types')
    name = models.CharField(max_length=100)
    ticket_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=GENERAL)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_quantity = models.PositiveIntegerField()
    sale_start = models.DateTimeField()
    sale_end = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ticket_types'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event']),
            models.Index(fields=['ticket_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['sale_start']),
            models.Index(fields=['sale_end']),
            models.Index(fields=['event', 'is_active']),
        ]

    def __str__(self):
        return f'{self.event.title} - {self.name}'

    @property
    def sold_count(self):
        return self.bookings.filter(
            status__in=['confirmed', 'pending']
        ).aggregate(total=models.Sum('quantity'))['total'] or 0

    @property
    def available_quantity(self):
        return self.total_quantity - self.sold_count

    @property
    def is_available(self):
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and
            self.available_quantity > 0 and
            self.sale_start <= now <= self.sale_end
        )
