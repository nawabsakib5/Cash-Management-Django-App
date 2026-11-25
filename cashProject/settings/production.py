import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403
from decouple import Csv, config

DEBUG = False

# ── Fail fast on unsafe configuration ──────────────────────────────────────────
if not SECRET_KEY or SECRET_KEY.startswith('django-insecure'):
    raise ImproperlyConfigured('SECRET_KEY must be set to a strong random value in production.')

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())
# Render injects the public hostname automatically.
_render_host = config('RENDER_EXTERNAL_HOSTNAME', default='')
if _render_host and _render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_render_host)
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured('Set ALLOWED_HOSTS (comma separated) for production.')

CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())
if _render_host:
    CSRF_TRUSTED_ORIGINS.append(f'https://{_render_host}')

# ── Database ───────────────────────────────────────────────────────────────────
# SQLite on an ephemeral disk loses all data on redeploy, so DATABASE_URL
# (PostgreSQL) is mandatory.
DATABASES = {
    'default': dj_database_url.parse(
        config('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# ── HTTPS / cookies / headers ──────────────────────────────────────────────────
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT     = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE   = True
CSRF_COOKIE_SECURE      = True
# Start low; raise to 31536000 (1 year) once HTTPS is confirmed working everywhere.
SECURE_HSTS_SECONDS     = config('SECURE_HSTS_SECONDS', default=3600, cast=int)
SECURE_REFERRER_POLICY  = 'same-origin'
X_FRAME_OPTIONS         = 'DENY'

# One proxy (Render's load balancer) sits in front of the app. If the audit log
# ever shows proxy IPs instead of real client IPs, raise this to 2.
TRUSTED_PROXY_COUNT = config('TRUSTED_PROXY_COUNT', default=1, cast=int)