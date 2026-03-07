from rest_framework import serializers
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.common.images import optimize_image_file
from apps.common.validators import validate_image_upload
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
        total_capacity = attrs.get('total_capacity')
        if total_capacity is not None and total_capacity <= 0:
            raise serializers.ValidationError('total_capacity must be greater than 0')
        return attrs

    def validate_banner_image(self, value):
        return validate_image_upload(value)

    def create(self, validated_data):
        image = validated_data.get('banner_image')
        if image:
            optimized = optimize_image_file(
                image,
                max_size=(settings.IMAGE_MAX_DIMENSION, settings.IMAGE_MAX_DIMENSION),
                quality=settings.IMAGE_OPTIMIZE_QUALITY,
            )
            if optimized:
                validated_data['banner_image'] = optimized
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image = validated_data.get('banner_image')
        if image:
            optimized = optimize_image_file(
                image,
                max_size=(settings.IMAGE_MAX_DIMENSION, settings.IMAGE_MAX_DIMENSION),
                quality=settings.IMAGE_OPTIMIZE_QUALITY,
            )
            if optimized:
                validated_data['banner_image'] = optimized
        return super().update(instance, validated_data)


class EventReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    rating = serializers.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        model = EventReview
        fields = ['id', 'rating', 'comment', 'user_name', 'created_at']
        read_only_fields = ['id', 'user_name', 'created_at']
