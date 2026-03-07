import os
from io import BytesIO

from PIL import Image
from django.core.files.base import ContentFile


SUPPORTED_FORMATS = {"JPEG", "JPG", "PNG", "WEBP"}


def optimize_image_file(image_file, *, max_size=(1600, 1600), quality=80):
    """
    Optimize an uploaded image in-memory and return a ContentFile.
    Returns None if optimization fails (caller should fallback to original).
    """
    if not image_file:
        return None

    try:
        image_file.seek(0)
        img = Image.open(image_file)
        original_format = (img.format or "JPEG").upper()

        if original_format not in SUPPORTED_FORMATS:
            original_format = "JPEG"

        if original_format in {"JPEG", "JPG"} and img.mode in {"RGBA", "P"}:
            img = img.convert("RGB")

        img.thumbnail(max_size, Image.LANCZOS)

        buffer = BytesIO()
        save_kwargs = {}
        if original_format in {"JPEG", "JPG", "WEBP"}:
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True

        if original_format == "WEBP":
            save_kwargs["method"] = 6

        img.save(buffer, format=original_format, **save_kwargs)
        buffer.seek(0)

        name = image_file.name or "optimized_image"
        base, _ = os.path.splitext(name)
        extension = ".jpg" if original_format in {"JPEG", "JPG"} else f".{original_format.lower()}"
        new_name = f"{base}{extension}"

        return ContentFile(buffer.read(), name=new_name)
    except Exception:
        return None
