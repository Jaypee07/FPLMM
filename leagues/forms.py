from django import forms

from .models import League


class LeagueCreateForm(forms.ModelForm):
    class Meta:
        model = League
        fields = ["name", "start_gameweek", "total_gameweeks", "include_chip_points"]
        help_texts = {
            "include_chip_points": "Only applies to leagues longer than 10 gameweeks.",
        }

    def clean(self):
        cleaned_data = super().clean()
        total_gameweeks = cleaned_data.get("total_gameweeks")

        # Force chip points off for short leagues regardless of what was submitted,
        # since the field is disabled client-side but a raw POST could bypass that.
        if total_gameweeks and total_gameweeks <= 10:
            cleaned_data["include_chip_points"] = False

        return cleaned_data


class JoinLeagueForm(forms.Form):
    code = forms.CharField(
        label="Invite Code",
        max_length=6,
        min_length=6,
    )

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()