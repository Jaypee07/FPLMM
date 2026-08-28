from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.core import mail

from accounts.models import User


FAKE_ENTRY = {"name": "John Doe", "team_name": "Doe's Dynamos"}


class RegistrationTests(TestCase):
    @patch("accounts.forms.fetch_fpl_entry", return_value=FAKE_ENTRY)
    def test_valid_registration_creates_inactive_user_and_sends_email(self, mock_fetch):
        response = self.client.post(reverse("register"), {
            "username": "newuser",
            "email": "newuser@example.com",
            "fpl_team_id": 999,
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })

        user = User.objects.get(username="newuser")
        self.assertFalse(user.is_active)
        self.assertEqual(user.fpl_manager_name, "John Doe")
        self.assertEqual(user.fpl_team_name, "Doe's Dynamos")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("verify", mail.outbox[0].body.lower())

    @patch("accounts.forms.fetch_fpl_entry", return_value=None)
    def test_invalid_fpl_id_blocks_registration(self, mock_fetch):
        response = self.client.post(reverse("register"), {
            "username": "baduser",
            "email": "bad@example.com",
            "fpl_team_id": 111,
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertFalse(User.objects.filter(username="baduser").exists())
        self.assertContains(response, "could not be found")

    @patch("accounts.forms.fetch_fpl_entry", return_value=FAKE_ENTRY)
    def test_duplicate_active_email_blocked(self, mock_fetch):
        User.objects.create_user(username="existing", email="taken@example.com", password="pass", is_active=True)
        response = self.client.post(reverse("register"), {
            "username": "newuser2",
            "email": "taken@example.com",
            "fpl_team_id": 999,
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertContains(response, "already exists")


class LoginTests(TestCase):
    def test_unverified_account_gets_specific_error(self):
        User.objects.create_user(username="unverified", password="pass", is_active=False)
        response = self.client.post(reverse("login"), {"username": "unverified", "password": "pass"})
        self.assertContains(response, "Check your email, or use the resend verification option")

    def test_verified_account_can_log_in(self):
        User.objects.create_user(username="verified", password="pass", is_active=True)
        response = self.client.post(reverse("login"), {"username": "verified", "password": "pass"})
        self.assertEqual(response.status_code, 302)  # redirect on success