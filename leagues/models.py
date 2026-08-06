import random
import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


def generate_league_code(length=6):
    """
    Generate a unique 6-character league invite code.
    """
    characters = string.ascii_uppercase + string.digits

    while True:
        code = "".join(random.choices(characters, k=length))

        if not League.objects.filter(code=code).exists():
            return code


class League(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_leagues",
    )

    name = models.CharField(max_length=100)

    code = models.CharField(
        max_length=6,
        unique=True,
        default=generate_league_code,
        editable=False,
    )

    start_gameweek = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(38),
        ]
    )

    total_gameweeks = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(38),
        ]
    )

    include_chip_points = models.BooleanField(
        default=False,
        help_text="Include chip bonus points when calculating standings."
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "League"
        verbose_name_plural = "Leagues"

    def clean(self):
        """
        Ensure the league does not extend beyond Gameweek 38.
        """
        end_gameweek = self.start_gameweek + self.total_gameweeks - 1

        if end_gameweek > 38:
            raise ValidationError({
                "total_gameweeks": (
                    f"This league would end in Gameweek {end_gameweek}. "
                    "A league cannot extend beyond Gameweek 38."
                )
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def end_gameweek(self):
        return self.start_gameweek + self.total_gameweeks - 1

    def __str__(self):
        return self.name