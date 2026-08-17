from django import forms
from django.contrib.auth.forms import UserCreationForm

from fpl.services import fetch_fpl_entry
from .models import User


class RegistrationForm(UserCreationForm):
    fpl_team_id = forms.IntegerField(
        label="FPL Team ID",
        help_text="Your official Fantasy Premier League Team ID.",
    )

    class Meta:
        model = User
        fields = ("username", "email", "fpl_team_id", "password1", "password2")

    def clean_fpl_team_id(self):
        team_id = self.cleaned_data["fpl_team_id"]
        entry = fetch_fpl_entry(team_id)
        if not entry:
            raise forms.ValidationError(
                "This FPL Team ID could not be found. Double-check and try again."
            )
        self.fpl_manager_name = entry["name"]
        return team_id

    def clean_email(self):
        email = self.cleaned_data["email"]
        existing = User.objects.filter(email=email).first()

        if existing:
            if existing.is_active:
                raise forms.ValidationError("An account with this email already exists.")
            else:
                # Unverified account sitting on this email — don't hard-block,
                # point them to resend instead of a dead end.
                raise forms.ValidationError(
                    "An account with this email is pending verification. "
                    "Use the 'Resend verification email' option instead of registering again."
                )
        return email


class ResendVerificationForm(forms.Form):
    email = forms.EmailField(label="Email")

    def clean_email(self):
        email = self.cleaned_data["email"]
        user = User.objects.filter(email=email).first()

        if not user:
            raise forms.ValidationError("No account found with this email.")
        if user.is_active:
            raise forms.ValidationError("This account is already verified. Try logging in.")

        self.user = user
        return email