from pathlib import Path

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Core ───────────────────────────────────────────────────────────────────────
# No insecure fallback here. dev.py supplies a throw-away key for local work and
# production.py refuses to start without a real one.
SECRET_KEY = config('SECRET_KEY', default='')
SITE_URL   = config('SITE_URL', default='')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'cashApp',
    'django_celery_beat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF     = 'cashProject.urls'
WSGI_APPLICATION = 'cashProject.wsgi.application'
ASGI_APPLICATION = 'cashProject.asgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'cashApp' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cashApp.context_processors.global_context',
            ],
        },
    },
]

AUTH_USER_MODEL    = 'cashApp.CustomUser'
LOGIN_URL          = 'login'
LOGIN_REDIRECT_URL = 'project_list'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Dhaka'
USE_I18N      = True
USE_TZ        = True

# ── Static files ───────────────────────────────────────────────────────────────
# STATICFILES_STORAGE was removed in Django 5.1; the STORAGES dict is the
# replacement (the old setting was being silently ignored).
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Email ──────────────────────────────────────────────────────────────────────
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT          = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL  = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)

# ── Redis / Celery / Channels ──────────────────────────────────────────────────
# With REDIS_URL set, Celery uses it as broker and Channels uses it as the layer.
# Without it (local dev, first deploy) everything falls back to in-process
# equivalents so the app still boots and nothing crashes on .delay().
REDIS_URL = config('REDIS_URL', default='')

CELERY_BROKER_URL     = REDIS_URL or 'memory://'
CELERY_RESULT_BACKEND = REDIS_URL or 'cache+memory://'
CELERY_TIMEZONE       = TIME_ZONE
# Run tasks inline unless a real worker is deployed (set CELERY_EAGER=False then).
CELERY_TASK_ALWAYS_EAGER    = config('CELERY_EAGER', default=not bool(REDIS_URL), cast=bool)
CELERY_TASK_EAGER_PROPAGATES = False

if REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {'hosts': [REDIS_URL]},
        },
    }
else:
    CHANNEL_LAYERS = {
        'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'},
    }

# ── Google Sheets sync ─────────────────────────────────────────────────────────
GOOGLE_SHEET_ID         = config('GOOGLE_SHEET_ID', default='')
GOOGLE_CREDENTIALS_JSON = config('GOOGLE_CREDENTIALS_JSON', default='')
GOOGLE_CREDENTIALS_FILE = config(
    'GOOGLE_CREDENTIALS_FILE', default=str(BASE_DIR / 'google_credentials.json')
)

# ── Logging ────────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {'format': '%(asctime)s %(levelname)s %(name)s: %(message)s'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'standard'},
    },
    'root': {
        'handlers': ['console'],
        'level': config('LOG_LEVEL', default='INFO'),
    },
}