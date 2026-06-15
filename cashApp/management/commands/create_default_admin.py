 
from django.core.management.base import BaseCommand
from cashApp.models import CustomUser


class Command(BaseCommand):
    help = 'Create default admin user if not exists'

    def handle(self, *args, **kwargs):
        if not CustomUser.objects.filter(username='admin').exists():
            CustomUser.objects.create_user(
                username  = 'admin',
                email     = 'admin@gmail.com',
                password  = '1234',
                user_type = 'admin',
            )
            self.stdout.write(self.style.SUCCESS('Default admin created.'))
        else:
            self.stdout.write('Admin already exists, skipping.')