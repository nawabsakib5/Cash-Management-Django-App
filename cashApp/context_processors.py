# cashApp/context_processors.py
from django.conf import settings

from .models import Transaction


def global_context(request):
    """
    Variables needed by base.html on every page:
      * pending_deletes  - badge count for admins (sidebar + topbar)
      * google_sheet_url - "Live Google Sheets" button (hidden when not configured)
    """
    ctx = {}

    sheet_id = getattr(settings, 'GOOGLE_SHEET_ID', '')
    if sheet_id:
        ctx['google_sheet_url'] = f'https://docs.google.com/spreadsheets/d/{sheet_id}/edit'

    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated and getattr(user, 'user_type', '') == 'admin':
        ctx['pending_deletes'] = Transaction.objects.filter(
            delete_requested=True, is_deleted=False
        ).count()

    return ctx