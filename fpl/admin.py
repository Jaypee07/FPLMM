# fpl/admin.py

from django.contrib import admin
from .models import Gameweek, WeeklyScore, Standing


@admin.register(Gameweek)
class GameweekAdmin(admin.ModelAdmin):
    list_display = ("number", "is_processed", "processed_at", "updated_at")
    list_filter = ("is_processed",)
    ordering = ("number",)
    readonly_fields = ("created_at", "updated_at")



@admin.register(WeeklyScore)
class WeeklyScoreAdmin(admin.ModelAdmin):
    list_display = ("league_member", "gameweek", "raw_points", "chip_used", "adjusted_points")
    list_filter = ("chip_used", "gameweek")
    ordering = ("gameweek", "league_member")
    readonly_fields = ("created_at", "updated_at")



@admin.register(Standing)
class StandingAdmin(admin.ModelAdmin):
    list_display = ("league_member", "gameweek", "rank", "total_points")
    list_filter = ("gameweek",)
    ordering = ("gameweek", "rank")
    readonly_fields = ("created_at", "updated_at")