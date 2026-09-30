from itertools import groupby

from django.core.cache import cache
from django.views.generic import TemplateView

from .services import fetch_bootstrap_teams, fetch_fixtures


def _get_labeled_fixtures():
    cached = cache.get("all_fixtures_data")
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
            "gameweek": fixture.get("event"),
        }

    labeled = [label(f) for f in fixtures]
    cache.set("all_fixtures_data", labeled, timeout=300)
    return labeled


def _group_by_gameweek(fixtures):
    """
    Groups a list of fixtures into [(gameweek_number, [fixtures...]), ...].
    Input must already be sorted by gameweek for groupby to work correctly.
    """
    def sort_key(f):
        return (f["gameweek"] is None, f["gameweek"] if f["gameweek"] is not None else 0)

    ordered = sorted(fixtures, key=sort_key)
    grouped = []
    for gw, group in groupby(ordered, key=lambda f: f["gameweek"]):
        grouped.append((gw, list(group)))
    return grouped


class FixturesView(TemplateView):
    template_name = "fpl/fixtures.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_fixtures = _get_labeled_fixtures()
        upcoming = [f for f in all_fixtures if not f["finished"]]
        upcoming_sorted = sorted(upcoming, key=lambda f: f["kickoff"] or "")
        context["grouped_fixtures"] = _group_by_gameweek(upcoming_sorted)
        return context


class ResultsView(TemplateView):
    template_name = "fpl/results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_fixtures = _get_labeled_fixtures()
        finished = [f for f in all_fixtures if f["finished"]]
        finished_sorted = sorted(finished, key=lambda f: f["kickoff"] or "", reverse=True)
        grouped = _group_by_gameweek(finished_sorted)
        context["grouped_results"] = sorted(grouped, key=lambda pair: (pair[0] is None, pair[0] or 0), reverse=True)
        return context