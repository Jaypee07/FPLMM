from django.contrib import admin
from django.core.cache import cache
from django.shortcuts import render
from django.urls import path, include

from fpl.services import fetch_bootstrap_teams, fetch_fixtures


def _get_home_teaser():
    cached = cache.get("home_teaser_data")
    if cached:
        return cached

    teams = fetch_bootstrap_teams()
    fixtures = fetch_fixtures()

    def label(fixture):
        home_team = teams.get(fixture["team_h"], {"name": "TBD", "badge_url": ""})
        away_team = teams.get(fixture["team_a"], {"name": "TBD", "badge_url": ""})
        return {
            "home": home_team["name"],
            "home_badge": home_team["badge_url"],
            "away": away_team["name"],
            "away_badge": away_team["badge_url"],
            "home_score": fixture.get("team_h_score"),
            "away_score": fixture.get("team_a_score"),
            "kickoff": fixture.get("kickoff_time"),
            "finished": fixture.get("finished"),
        }

    labeled = [label(f) for f in fixtures]
    finished = sorted([f for f in labeled if f["finished"]], key=lambda f: f["kickoff"], reverse=True)[:3]
    upcoming = sorted([f for f in labeled if not f["finished"] and f["kickoff"]], key=lambda f: f["kickoff"])[:3]

    data = {"recent_results": finished, "next_fixtures": upcoming}
    cache.set("home_teaser_data", data, timeout=300)
    return data


def root_view(request):
    context = _get_home_teaser()
    return render(request, "home.html", context)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", root_view, name="home"),
    path("accounts/", include("accounts.urls")),
    path("leagues/", include("leagues.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("", include("fpl.urls")),
]