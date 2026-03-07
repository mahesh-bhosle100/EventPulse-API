from rest_framework import serializers
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from apps.common.images import optimize_image_file
from apps.common.validators import validate_image_upload
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone', 'role', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match'})
        if attrs.get('role') == User.ADMIN:
            raise serializers.ValidationError({'role': 'Cannot register as admin'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone', 'role', 'profile_photo', 'created_at']
        read_only_fields = ['id', 'email', 'role', 'created_at']

    def validate_phone(self, value):
        if value and not value.isdigit():
            raise serializers.ValidationError('Phone must contain digits only')
        if value and not (7 <= len(value) <= 15):
            raise serializers.ValidationError('Phone length must be 7 to 15 digits')
        return value

    def validate_profile_photo(self, value):
        return validate_image_upload(value)

    def update(self, instance, validated_data):
        image = validated_data.get('profile_photo')
        if image:
            optimized = optimize_image_file(
                image,
                max_size=(settings.IMAGE_MAX_DIMENSION, settings.IMAGE_MAX_DIMENSION),
                quality=settings.IMAGE_OPTIMIZE_QUALITY,
            )
            if optimized:
                validated_data['profile_photo'] = optimized
        return super().update(instance, validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect')
        return value
