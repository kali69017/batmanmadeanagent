"""Create (or set the password for) a client user account.

Usage:
    python manage.py create_client <username> <email> [--password <pw>]

If --password is omitted, prompts are avoided (stdin is non-interactive here);
set the password via Django admin or re-run with --password.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create a client user with email + password."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("email")
        parser.add_argument("--password", default=None)
        parser.add_argument("--staff", action="store_true", help="Mark as staff (admin access).")

    def handle(self, *args, **options):
        User = get_user_model()
        username = options["username"]
        email = options["email"]
        password = options["password"]

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )
        if not created:
            user.email = email

        if password:
            user.set_password(password)
        if options["staff"]:
            user.is_staff = True
            user.is_superuser = True
        user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(
            f"{action} client '{username}' <{email}>."
        ))
        if not password:
            self.stdout.write(self.style.WARNING(
                "No --password given. Set one via admin or re-run with --password."
            ))
