import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from crm.services import ensure_roles


class Command(BaseCommand):
    help = "Create or update the first online admin user from environment variables."

    def handle(self, *args, **options):
        username = os.getenv("ADMIN_USERNAME", "").strip()
        email = os.getenv("ADMIN_EMAIL", "").strip()
        password = os.getenv("ADMIN_PASSWORD", "")

        missing = [
            name
            for name, value in (
                ("ADMIN_USERNAME", username),
                ("ADMIN_EMAIL", email),
                ("ADMIN_PASSWORD", password),
            )
            if not value
        ]
        if missing:
            raise CommandError("Missing required environment variable(s): " + ", ".join(missing))

        ensure_roles()
        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        manager_group = user.groups.model.objects.get(name="Manager")
        user.groups.add(manager_group)

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} admin user '{username}'."))
