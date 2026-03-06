import django_filters
from .models import Event


class EventFilter(django_filters.FilterSet):
    city = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.NumberFilter(field_name='category__id')
    status = django_filters.CharFilter()
    is_free = django_filters.BooleanFilter()
    start_after = django_filters.DateTimeFilter(field_name='start_datetime', lookup_expr='gte')
    start_before = django_filters.DateTimeFilter(field_name='start_datetime', lookup_expr='lte')

    class Meta:
        model = Event
        fields = ['city', 'category', 'status', 'is_free']
