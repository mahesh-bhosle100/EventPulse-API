from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

# Use console email in dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Use local file storage in dev (no Cloudinary needed)
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
