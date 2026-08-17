"""Create (or rotate) a login token for a user.

Usage:
    python manage.py issue_token <username> [--rotate]
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = "Create a user (if missing) and print a new login token."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("--rotate", action="store_true", help="Revoke the existing token and issue a new one.")

    def handle(self, *args, **options):
        username = options["username"]
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"is_active": True},
        )
        if created:
            user.set_unusable_password()
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created user '{username}'."))
        token = Token.objects.filter(user=user).first()
        if token and options["rotate"]:
            token.delete()
            token = None
        if token is None:
            token = Token.objects.create(user=user)
            self.stdout.write(self.style.SUCCESS(f"New token for '{username}':"))
        else:
            self.stdout.write(self.style.WARNING(f"Existing token for '{username}' (use --rotate to replace):"))
        self.stdout.write(token.key)
