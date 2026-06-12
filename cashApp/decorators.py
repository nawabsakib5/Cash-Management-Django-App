# cashApp/decorators.py

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import AuditLog


# ── Permission Decorators ──────────────────────────────────────────────────────

def admin_required(view_func):
    """Only user_type='admin' can access this view."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.user_type != 'admin':
            messages.error(request, "This page is accessible to Admins only.")
            return redirect('project_list')
        return view_func(request, *args, **kwargs)
    return wrapper


def not_frozen(view_func):
    """Frozen users can log in but cannot perform any actions."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_frozen:
            messages.error(request, "Your account has been frozen. Please contact the Admin.")
            return redirect('project_list')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Audit Log Helper ───────────────────────────────────────────────────────────

def log_action(actor, action, target=None, detail='', request=None):
    """
    Helper to create an AuditLog entry from anywhere in the codebase.

    Usage:
        log_action(request.user, 'create', target=transaction, request=request)
        log_action(request.user, 'freeze', detail=f'User: {user.username}', request=request)
    """
    ip = None
    if request:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')

    target_type = ''
    target_id   = None
    target_repr = ''

    if target is not None:
        target_type = type(target).__name__
        target_id   = getattr(target, 'pk', None)
        target_repr = str(target)[:255]

    AuditLog.objects.create(
        actor       = actor,
        action      = action,
        target_type = target_type,
        target_id   = target_id,
        target_repr = target_repr,
        detail      = detail[:500] if detail else '',
        ip_address  = ip,
    )