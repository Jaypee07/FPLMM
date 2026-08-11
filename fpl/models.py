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


class WeeklyScore(models.Model):
    class Chip(models.TextChoices):
        BENCH_BOOST = "bboost", "Bench Boost"
        TRIPLE_CAPTAIN = "3xc", "Triple Captain"
        WILDCARD = "wildcard", "Wildcard"
        FREE_HIT = "freehit", "Free Hit"

    league_member = models.ForeignKey(
        "leagues.LeagueMember",
        on_delete=models.CASCADE,
        related_name="weekly_scores",
    )

    gameweek = models.ForeignKey(
        Gameweek,
        on_delete=models.CASCADE,
        related_name="weekly_scores",
    )

    raw_points = models.IntegerField(
        help_text="Official FPL points for this gameweek, chip effects included."
    )

    chip_used = models.CharField(
        max_length=10,
        choices=Chip.choices,
        null=True,
        blank=True,
    )

    adjusted_points = models.IntegerField(
        help_text="raw_points with bench boost / triple captain bonus removed. "
                   "Equal to raw_points if no scoring chip was used."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["league_member", "gameweek"],
                name="unique_weeklyscore_per_member_per_gw",
            )
        ]
        ordering = ["gameweek", "league_member"]
        verbose_name = "Weekly Score"
        verbose_name_plural = "Weekly Scores"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.league_member} - GW{self.gameweek.number}: {self.raw_points}"

    @property
    def score_for_standing(self):
        if self.league_member.league.include_chip_points:
            return self.raw_points
        return self.adjusted_points


# fpl/models.py

class Standing(models.Model):
    league_member = models.ForeignKey(
        "leagues.LeagueMember",
        on_delete=models.CASCADE,
        related_name="standings",
    )

    gameweek = models.ForeignKey(
        Gameweek,
        on_delete=models.CASCADE,
        related_name="standings",
    )

    total_points = models.IntegerField(
        help_text="Cumulative points for this member from the league's "
                   "start_gameweek through this gameweek."
    )

    rank = models.PositiveSmallIntegerField(
        help_text="Member's rank within the league as of this gameweek."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["league_member", "gameweek"],
                name="unique_standing_per_member_per_gw",
            )
        ]
        ordering = ["gameweek", "rank"]
        verbose_name = "Standing"
        verbose_name_plural = "Standings"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.league_member} - GW{self.gameweek.number}: #{self.rank} ({self.total_points} pts)"