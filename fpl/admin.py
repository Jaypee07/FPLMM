# fpl/admin.py

from django.contrib import admin
from .models import Gameweek


@admin.register(Gameweek)
class GameweekAdmin(admin.ModelAdmin):
    list_display = ("number", "is_processed", "processed_at", "updated_at")
    list_filter = ("is_processed",)
    ordering = ("number",)
    readonly_fields = ("created_at", "updated_at")