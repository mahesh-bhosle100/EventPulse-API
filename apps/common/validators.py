from django.conf import settings
from rest_framework import serializers


def validate_image_upload(image_file, *, max_mb=None):
    if not image_file:
        return image_file

    max_mb = max_mb or getattr(settings, "IMAGE_MAX_UPLOAD_MB", 5)
    max_bytes = max_mb * 1024 * 1024

    if image_file.size > max_bytes:
        raise serializers.ValidationError(
            f"Image file too large. Max allowed size is {max_mb} MB."
        )

    return image_file
