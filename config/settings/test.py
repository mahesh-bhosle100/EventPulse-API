from .base import *

DEBUG = True
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test.sqlite3',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
