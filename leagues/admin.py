from django.contrib import admin

from .models import League


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "code",
        "start_gameweek",
        "total_gameweeks",
        "include_chip_points",
        "is_active",
        "created_at",
    )

    list_filter = (
        "include_chip_points",
        "is_active",
    )

    search_fields = (
        "name",
        "code",
        "owner__username",
    )

    readonly_fields = (
        "code",
        "created_at",
        "updated_at",
    )