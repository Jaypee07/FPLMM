from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User


class Command(BaseCommand):
    help = "Deletes unverified (is_active=False) accounts older than 3 days."

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=3)
        stale = User.objects.filter(is_active=False, date_joined__lt=cutoff)
        count = stale.count()
        stale.delete()
        self.stdout.write(f"Deleted {count} stale unverified account(s).")