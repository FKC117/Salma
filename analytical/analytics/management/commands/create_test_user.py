from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a test user for frontend testing'

    def handle(self, *args, **options):
        username = 'testuser'
        password = 'testpass123'
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User "{username}" already exists')
            )
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                email='test@example.com'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created user "{username}"')
            )
            self.stdout.write(f'Username: {username}')
            self.stdout.write(f'Password: {password}')
