from django.contrib import admin, messages

from .models import Gameweek, WeeklyScore, Standing
from .processing import process_gameweek


@admin.action(description="Process selected gameweek(s)")
def process_gameweeks_action(modeladmin, request, queryset):
    for gameweek in queryset:
        if gameweek.is_processed:
            messages.warning(request, f"Gameweek {gameweek.number} was already processed — reprocessing.")

        result = process_gameweek(gameweek)

        messages.success(
            request,
            f"GW{gameweek.number}: {result['members_processed']} member(s) scored across "
            f"{result['leagues_updated']} league(s)."
        )

        for error in result["errors"]:
            messages.error(request, f"GW{gameweek.number}: {error}")


@admin.register(Gameweek)
class GameweekAdmin(admin.ModelAdmin):
    list_display = ("number", "is_processed", "processed_at", "updated_at")
    list_filter = ("is_processed",)
    ordering = ("number",)
    readonly_fields = ("created_at", "updated_at")
    actions = [process_gameweeks_action]


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