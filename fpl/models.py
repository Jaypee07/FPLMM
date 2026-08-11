# fpl/models.py

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Gameweek(models.Model):
    number = models.PositiveSmallIntegerField(
        unique=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(38),
        ],
        help_text="Official FPL gameweek number (1-38).",
    )

    is_processed = models.BooleanField(default=False)

    processed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["number"]
        verbose_name = "Gameweek"
        verbose_name_plural = "Gameweeks"

    def clean(self):
        if self.processed_at and not self.is_processed:
            raise ValidationError({
                "processed_at": "processed_at should only be set when is_processed is True."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Gameweek {self.number}"