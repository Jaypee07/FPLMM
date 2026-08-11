from django.contrib import admin

from .models import League, LeagueMember


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "code",
        "start_gameweek",
        "total_gameweeks",
        "end_gameweek",
        "include_chip_points",
        "is_active",
        "created_at",
    )
    search_fields = (
        "name",
        "code",
        "owner__username",
    )
    list_filter = (
        "is_active",
        "include_chip_points",
    )
    readonly_fields = (
        "code",
        "created_at",
        "updated_at",
    )


@admin.register(LeagueMember)
class LeagueMemberAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "league",
        "joined_at",
    )
    search_fields = (
        "user__username",
        "league__name",
        "league__code",
    )
    list_filter = (
        "league",
    )
    readonly_fields = (
        "joined_at",
    )