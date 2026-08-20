from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    fpl_team_id = models.PositiveIntegerField(
        unique=True,
        null=True,
        blank=True,
        help_text="Official Fantasy Premier League Team ID"
    )

    fpl_manager_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Manager name as registered on the official FPL platform."
    )

    fpl_team_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="FPL team name as registered on the official FPL platform."
    )

    def __str__(self):
        return self.username