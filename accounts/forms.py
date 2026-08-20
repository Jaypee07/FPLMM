from django import forms
from django.contrib.auth.forms import UserCreationForm

from fpl.services import fetch_fpl_entry
from .models import User


INPUT_CLASSES = (
    "w-full border border-divider rounded-2xl px-4 py-3 text-ink "
    "focus:outline-none focus:ring-2 focus:ring-lime-400 transition"
)


class TailwindStyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {INPUT_CLASSES}".strip()


class RegistrationForm(TailwindStyledFormMixin, UserCreationForm):
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
        self.fpl_team_name = entry["team_name"]
        return team_id

    def clean_email(self):
        email = self.cleaned_data["email"]
        existing = User.objects.filter(email=email).first()

        if existing:
            if existing.is_active:
                raise forms.ValidationError("An account with this email already exists.")
            else:
                raise forms.ValidationError(
                    "An account with this email is pending verification. "
                    "Use the 'Resend verification email' option instead of registering again."
                )
        return email


class ResendVerificationForm(TailwindStyledFormMixin, forms.Form):
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