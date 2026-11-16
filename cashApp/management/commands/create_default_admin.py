from decouple import config
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from cashApp.models import AdminProfile, CustomUser


class Command(BaseCommand):
    help = (
        'Create the first admin from ADMIN_USERNAME / ADMIN_EMAIL / ADMIN_PASSWORD '
        'environment variables. Does nothing if they are not set or the user exists.'
    )

    def handle(self, *args, **options):
        username = config('ADMIN_USERNAME', default='admin')
        email    = config('ADMIN_EMAIL', default='')
        password = config('ADMIN_PASSWORD', default='')

        if not email or not password:
            self.stdout.write(self.style.WARNING(
                'ADMIN_EMAIL / ADMIN_PASSWORD not set - skipping admin creation.'
            ))
            return

        if CustomUser.objects.filter(username=username).exists():
            self.stdout.write('Admin already exists, skipping.')
            return

        if CustomUser.objects.filter(email__iexact=email).exists():
            raise CommandError(f'A user with email {email} already exists.')

        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError('ADMIN_PASSWORD is too weak: ' + ' '.join(exc.messages))

        user = CustomUser.objects.create_user(
            username=username, email=email, password=password, user_type='admin',
        )
        AdminProfile.objects.get_or_create(user=user)
        self.stdout.write(self.style.SUCCESS(f"Admin '{username}' created."))