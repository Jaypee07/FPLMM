from django import forms
from django.core.exceptions import ValidationError

from .models import League


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


class LeagueCreateForm(TailwindStyledFormMixin, forms.ModelForm):
    class Meta:
        model = League
        fields = ["name", "start_gameweek", "total_gameweeks", "include_chip_points"]
        help_texts = {
            "include_chip_points": "Only applies to leagues longer than 10 gameweeks.",
        }

    def clean(self):
        cleaned_data = super().clean()
        total_gameweeks = cleaned_data.get("total_gameweeks")

        if total_gameweeks and total_gameweeks <= 10:
            cleaned_data["include_chip_points"] = False

        return cleaned_data


class JoinLeagueForm(TailwindStyledFormMixin, forms.Form):
    code = forms.CharField(
        label="Invite Code",
        max_length=6,
        min_length=6,
    )

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()