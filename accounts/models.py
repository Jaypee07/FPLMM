from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    fpl_team_id = models.PositiveIntegerField(
        unique=True,
        null=True,
        blank=True,
        help_text="Official Fantasy Premier League Team ID"
    )

    def __str__(self):
        return self.username