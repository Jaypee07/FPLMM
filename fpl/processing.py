from django.utils import timezone

from leagues.models import League, LeagueMember
from .models import Gameweek, WeeklyScore, Standing
from .services import fetch_gameweek_picks, fetch_gameweek_live_points, compute_scores_from_picks


def process_gameweek(gameweek):
    """
    Processes a single Gameweek across every league currently covering it.
    Fetches picks per member, computes/stores WeeklyScore, then recomputes
    cumulative Standing for every affected league.

    Returns a summary dict for admin feedback.
    """
    live_points = fetch_gameweek_live_points(gameweek.number)

    leagues = [
        league for league in League.objects.filter(is_active=True)
        if league.start_gameweek <= gameweek.number <= league.end_gameweek
    ]

    members_processed = 0
    errors = []

    for league in leagues:
        for member in league.members.select_related("user"):
            team_id = member.user.fpl_team_id
            if not team_id:
                errors.append(f"{member.user.username} has no FPL Team ID set.")
                continue

            picks_data = fetch_gameweek_picks(team_id, gameweek.number)
            if not picks_data:
                errors.append(f"Could not fetch picks for {member.user.username} (GW{gameweek.number}).")
                continue

            raw_points, chip_used, adjusted_points = compute_scores_from_picks(picks_data, live_points)

            WeeklyScore.objects.update_or_create(
                league_member=member,
                gameweek=gameweek,
                defaults={
                    "raw_points": raw_points,
                    "chip_used": chip_used,
                    "adjusted_points": adjusted_points,
                },
            )
            members_processed += 1

        _recompute_standing(league, gameweek)

    gameweek.is_processed = True
    gameweek.processed_at = timezone.now()
    gameweek.save()

    return {
        "members_processed": members_processed,
        "leagues_updated": len(leagues),
        "errors": errors,
    }


def _recompute_standing(league, up_to_gameweek):
    """
    Recomputes cumulative Standing for every member of a league, from
    league.start_gameweek through up_to_gameweek, and stores ranks.
    Ties share the same rank (competition ranking: 1, 2, 2, 4).
    """
    totals = []
    for member in league.members.all():
        scores = WeeklyScore.objects.filter(
            league_member=member,
            gameweek__number__gte=league.start_gameweek,
            gameweek__number__lte=up_to_gameweek.number,
        )
        total = sum(ws.score_for_standing for ws in scores)
        totals.append((member, total))

    totals.sort(key=lambda pair: pair[1], reverse=True)

    rank = 0
    previous_total = None
    for index, (member, total) in enumerate(totals, start=1):
        if total != previous_total:
            rank = index
        previous_total = total

        Standing.objects.update_or_create(
            league_member=member,
            gameweek=up_to_gameweek,
            defaults={"total_points": total, "rank": rank},
        )