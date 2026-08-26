from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Sum
from .models import Transaction, Project


def get_live_stats():
    total_income = Transaction.objects.filter(
        type='income', is_deleted=False
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_expense = Transaction.objects.filter(
        type='expense', is_deleted=False
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_projects = Project.objects.count()

    recent_transactions = list(
        Transaction.objects.filter(is_deleted=False)
        .order_by('-date')[:5]
        .values('title', 'amount', 'type', 'date')
    )

    for tx in recent_transactions:
        tx['date'] = str(tx['date'])
        tx['amount'] = str(tx['amount'])

    return {
        'total_income':        str(total_income),
        'total_expense':       str(total_expense),
        'balance':             str(total_income - total_expense),
        'total_projects':      total_projects,
        'recent_transactions': recent_transactions,
    }


@shared_task
def send_dashboard_update():
    channel_layer = get_channel_layer()
    data = get_live_stats()
    async_to_sync(channel_layer.group_send)(
        'dashboard',
        {
            'type': 'dashboard.update',
            'data': data,
        }
    )