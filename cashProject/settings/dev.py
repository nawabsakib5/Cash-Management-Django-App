from .base import *  # noqa: F401,F403
from decouple import config

DEBUG = True

# Throw-away key so local development works with an empty .env
SECRET_KEY = SECRET_KEY or 'django-insecure-dev-only-not-for-production'

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,[::1]').split(',')

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# PostgreSQL when DB_NAME is configured, otherwise a zero-setup SQLite file.
if config('DB_NAME', default=''):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# No collectstatic needed locally (the manifest storage would 500 on /admin/).
STORAGES = {
    **STORAGES,
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}

# Print emails to the console unless real SMTP credentials are configured.
if not EMAIL_HOST_USER:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'