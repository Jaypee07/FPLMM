import requests

def fetch_fpl_entry(team_id):
    """
    Returns dict with manager name if valid, or None if not found/unreachable.
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