from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from receipts.models import Receipt


class Command(BaseCommand):
    help = "Assign receipts with user=NULL to a specified user (by email)."

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Email of the user to assign orphan receipts to.")
        parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes.")

    def handle(self, *args, **options):
        email = options["email"]
        dry_run = options["dry_run"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f"User with email '{email}' does not exist.")

        orphans = Receipt.objects.filter(user__isnull=True)
        count = orphans.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No orphan receipts found."))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING(f"[DRY RUN] Would assign {count} orphan receipt(s) to {email}."))
            return

        updated = orphans.update(user=user)
        self.stdout.write(self.style.SUCCESS(f"Assigned {updated} orphan receipt(s) to {email}."))
