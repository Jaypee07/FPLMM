# accounts/management/commands/send_test_verification.py

import webbrowser

from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import User
from accounts.tokens import email_verification_token


class Command(BaseCommand):
    help = "Generates a verification link for a given username and opens it in the browser."

    def add_arguments(self, parser):
        parser.add_argument("username", type=str)

    def handle(self, *args, **options):
        username = options["username"]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"No user named '{username}'")

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = email_verification_token.make_token(user)
        path = reverse("verify-email", kwargs={"uidb64": uid, "token": token})
        url = f"http://127.0.0.1:8000{path}"

        self.stdout.write(f"Opening: {url}")
        webbrowser.open(url)