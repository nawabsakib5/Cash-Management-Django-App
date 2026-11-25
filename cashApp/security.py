# cashApp/security.py
"""
Small, dependency-free security helpers:

  * get_client_ip()      - client IP that cannot be spoofed via X-Forwarded-For
  * login lockout        - per (username, IP) and per IP, stored in Django's cache
  * hit_rate_limit()     - generic fixed-window rate limit (sign-up, change-password)

Counters live in the default cache: in-process (LocMem) by default, shared across
processes when REDIS_URL is configured (see CACHES in settings/base.py).
"""
import hashlib
import ipaddress
import time

from django.conf import settings
from django.core.cache import cache


# ── Client IP ──────────────────────────────────────────────────────────────────

def get_client_ip(request):
    """
    Return the client IP as a validated string, or None.

    X-Forwarded-For is only trusted when TRUSTED_PROXY_COUNT > 0, and then only the
    entry appended by our own proxy (counted from the right) is used. Anything the
    client puts at the left of the header is ignored, so it cannot be spoofed.
    """
    candidate = request.META.get('REMOTE_ADDR', '')
    proxies = getattr(settings, 'TRUSTED_PROXY_COUNT', 0)

    if proxies > 0:
        header = request.META.get('HTTP_X_FORWARDED_FOR', '')
        parts = [p.strip() for p in header.split(',') if p.strip()]
        if len(parts) >= proxies:
            candidate = parts[-proxies]

    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None


# ── Cache counters ─────────────────────────────────────────────────────────────

def _key(*parts):
    # Hash so user-supplied text can never produce an invalid/oversized cache key.
    raw = '|'.join(str(p) for p in parts)
    return 'sec:' + hashlib.sha256(raw.encode('utf-8')).hexdigest()


def _incr(key, window):
    """Increment a counter that expires `window` seconds after its first hit."""
    cache.add(key, 0, window)
    try:
        return cache.incr(key)
    except ValueError:          # key expired between add() and incr()
        cache.set(key, 1, window)
        return 1


# ── Login lockout ──────────────────────────────────────────────────────────────

def _login_keys(request, identifier):
    ip = get_client_ip(request) or 'unknown'
    ident = (identifier or '').strip().lower()
    return {
        'count_user': _key('login-count-user', ident, ip),
        'count_ip':   _key('login-count-ip', ip),
        'lock_user':  _key('login-lock-user', ident, ip),
        'lock_ip':    _key('login-lock-ip', ip),
    }


def login_lock_remaining(request, identifier):
    """Seconds left on a lockout for this (identifier, IP) or IP; 0 when not locked."""
    keys = _login_keys(request, identifier)
    now = time.time()
    remaining = 0
    for name in ('lock_user', 'lock_ip'):
        until = cache.get(keys[name])
        if until:
            remaining = max(remaining, int(until - now))
    return max(remaining, 0)


def record_login_failure(request, identifier):
    """Count a failed login. Returns True if this failure triggered a lockout."""
    keys = _login_keys(request, identifier)
    window = settings.LOGIN_LOCKOUT_SECONDS
    locked = False

    if _incr(keys['count_user'], window) >= settings.LOGIN_MAX_ATTEMPTS:
        cache.set(keys['lock_user'], time.time() + window, window)
        cache.delete(keys['count_user'])
        locked = True

    if _incr(keys['count_ip'], window) >= settings.LOGIN_IP_MAX_ATTEMPTS:
        cache.set(keys['lock_ip'], time.time() + window, window)
        cache.delete(keys['count_ip'])
        locked = True

    return locked


def clear_login_failures(request, identifier):
    """Reset the per-account counters after a successful login."""
    keys = _login_keys(request, identifier)
    cache.delete_many([keys['count_user'], keys['lock_user']])


# ── Generic rate limit ─────────────────────────────────────────────────────────

def hit_rate_limit(scope, request, limit, window, extra=''):
    """Count one attempt. Returns True while still allowed, False once over `limit`."""
    ip = get_client_ip(request) or 'unknown'
    return _incr(_key('rl', scope, ip, extra), window) <= limit