import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db.models import Sum
from .models import Transaction, Project


class DashboardConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # The dashboard broadcasts system-wide totals across every project, so only
        # admins may listen. Anonymous, frozen and regular users are refused.
        # (scope['user'] is already resolved by AuthMiddlewareStack.)
        user = self.scope.get('user')
        if (
            user is None
            or not user.is_authenticated
            or getattr(user, 'is_frozen', False)
            or getattr(user, 'user_type', '') != 'admin'
        ):
            await self.close(code=4401)
            return

        await self.channel_layer.group_add('dashboard', self.channel_name)
        await self.accept()
        # connect হলেই সাথে সাথে current data পাঠাও
        data = await self.get_stats()
        await self.send(text_data=json.dumps(data))

    async def disconnect(self, close_code):
        # group_discard is harmless if the socket was rejected in connect().
        await self.channel_layer.group_discard('dashboard', self.channel_name)

    async def receive(self, text_data):
        # browser থেকে কিছু আসলে fresh data পাঠাও
        data = await self.get_stats()
        await self.send(text_data=json.dumps(data))

    async def dashboard_update(self, event):
        # Celery task trigger করলে এখানে আসে, browser এ push হয়
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def get_stats(self):
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

        # date serialize করো
        for tx in recent_transactions:
            tx['date'] = str(tx['date'])
            tx['amount'] = str(tx['amount'])

        return {
            'total_income':          str(total_income),
            'total_expense':         str(total_expense),
            'balance':               str(total_income - total_expense),
            'total_projects':        total_projects,
            'recent_transactions':   recent_transactions,
        }