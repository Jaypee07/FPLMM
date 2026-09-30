import requests


def fetch_fpl_entry(team_id):
    """
    Checks whether a Team ID resolves to a real manager. Used at registration.
    """
    url = f"https://fantasy.premierleague.com/api/entry/{team_id}/"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "name": f"{data['player_first_name']} {data['player_last_name']}",
                "team_name": data.get("name"),
            }
    except requests.RequestException:
        pass
    return None


def fetch_gameweek_picks(team_id, gameweek_number):
    url = f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{gameweek_number}/picks/"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None


def fetch_gameweek_live_points(gameweek_number):
    """
    Returns {player_id: points} for every player in the league that gameweek.
    Fetch once per gameweek, reuse across all managers being processed.
    """
    url = f"https://fantasy.premierleague.com/api/event/{gameweek_number}/live/"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                element["id"]: element["stats"]["total_points"]
                for element in data.get("elements", [])
            }
    except requests.RequestException:
        pass
    return {}


def compute_scores_from_picks(picks_data, live_points):
    """
    picks_data: raw response from fetch_gameweek_picks()
    live_points: dict from fetch_gameweek_live_points(), {player_id: points}

    Returns (raw_points, chip_used, adjusted_points).
    """
    entry_history = picks_data.get("entry_history", {})
    raw_points = entry_history.get("points", 0)
    chip_used = picks_data.get("active_chip")
    picks = picks_data.get("picks", [])

    adjusted_points = raw_points

    if chip_used == "bboost":
        bench_bonus = sum(
            live_points.get(pick["element"], 0)
            for pick in picks
            if pick.get("position", 0) >= 12
        )
        adjusted_points = raw_points - bench_bonus

    elif chip_used == "3xc":
        captain_pick = next((p for p in picks if p.get("is_captain")), None)
        if captain_pick:
            captain_points = live_points.get(captain_pick["element"], 0)
            adjusted_points = raw_points - captain_points

    return raw_points, chip_used, adjusted_points


def fetch_bootstrap_teams():
    """
    Returns {team_id: {"name": ..., "badge_url": ...}} for all 20 PL teams.
    """
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                team["id"]: {
                    "name": team["name"],
                    "badge_url": f"https://resources.premierleague.com/premierleague/badges/70/t{team['code']}.png",
                }
                for team in data.get("teams", [])
            }
    except requests.RequestException:
        pass
    return {}


def fetch_fixtures():
    """
    Returns the raw fixtures list from the FPL API — each fixture has
    team_h, team_a, team_h_score, team_a_score, kickoff_time, finished.
    """
    url = "https://fantasy.premierleague.com/api/fixtures/"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return []