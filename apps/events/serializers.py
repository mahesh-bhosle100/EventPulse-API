from rest_framework import serializers
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Event, Category, EventReview


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class EventListSerializer(serializers.ModelSerializer):
    organizer_name = serializers.CharField(source='organizer.full_name', read_only=True)
    available_seats = serializers.ReadOnlyField()
    is_sold_out = serializers.ReadOnlyField()
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'banner_image', 'venue', 'city',
            'start_datetime', 'end_datetime', 'status',
            'total_capacity', 'available_seats', 'is_sold_out',
            'is_free', 'organizer_name', 'category_name', 'created_at'
        ]


class EventDetailSerializer(serializers.ModelSerializer):
    organizer_name = serializers.CharField(source='organizer.full_name', read_only=True)
    available_seats = serializers.ReadOnlyField()
    is_sold_out = serializers.ReadOnlyField()
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False
    )

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'banner_image', 'venue', 'city', 'address',
            'start_datetime', 'end_datetime', 'status', 'total_capacity',
            'available_seats', 'is_sold_out', 'is_free',
            'organizer_name', 'category', 'category_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organizer_name', 'available_seats', 'is_sold_out', 'created_at', 'updated_at']

    def validate(self, attrs):
        if attrs.get('start_datetime') and attrs.get('end_datetime'):
            if attrs['end_datetime'] <= attrs['start_datetime']:
                raise serializers.ValidationError('end_datetime must be after start_datetime')
        return attrs


class EventReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    rating = serializers.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        model = EventReview
        fields = ['id', 'rating', 'comment', 'user_name', 'created_at']
        read_only_fields = ['id', 'user_name', 'created_at']
