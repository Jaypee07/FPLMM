from django.test import TestCase
from django.core.exceptions import ValidationError
from unittest.mock import patch

from accounts.models import User
from leagues.models import League, LeagueMember
from fpl.models import Gameweek, WeeklyScore, Standing
from fpl.services import compute_scores_from_picks
from fpl.processing import process_gameweek


class GameweekModelTests(TestCase):
    def test_valid_gameweek_created(self):
        gw = Gameweek.objects.create(number=1)
        self.assertEqual(str(gw), "Gameweek 1")

    def test_number_out_of_range_rejected(self):
        with self.assertRaises(ValidationError):
            Gameweek.objects.create(number=39)

    def test_duplicate_number_rejected(self):
        Gameweek.objects.create(number=5)
        with self.assertRaises(ValidationError):
            Gameweek.objects.create(number=5)


class WeeklyScoreModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass", fpl_team_id=1)
        self.league = League.objects.create(owner=self.owner, name="Test League", start_gameweek=1, total_gameweeks=4)
        self.member = LeagueMember.objects.create(league=self.league, user=self.owner)
        self.gw = Gameweek.objects.create(number=1)

    def test_duplicate_weeklyscore_rejected(self):
        WeeklyScore.objects.create(
            league_member=self.member, gameweek=self.gw, raw_points=60, adjusted_points=60,
        )
        with self.assertRaises(ValidationError):
            WeeklyScore.objects.create(
                league_member=self.member, gameweek=self.gw, raw_points=70, adjusted_points=70,
            )

    def test_score_for_standing_respects_league_setting(self):
        ws = WeeklyScore.objects.create(
            league_member=self.member, gameweek=self.gw,
            raw_points=90, chip_used=WeeklyScore.Chip.TRIPLE_CAPTAIN, adjusted_points=70,
        )

        self.league.include_chip_points = False
        self.league.save()
        self.assertEqual(ws.score_for_standing, 70)

        self.league.include_chip_points = True
        self.league.save()
        self.assertEqual(ws.score_for_standing, 90)


class ComputeScoresFromPicksTests(TestCase):
    """
    Pure logic tests for chip-adjustment math — no DB, no API calls.
    """

    def test_no_chip_raw_equals_adjusted(self):
        picks_data = {
            "entry_history": {"points": 60},
            "active_chip": None,
            "picks": [{"element": 101, "position": 1, "is_captain": True}],
        }
        raw, chip, adjusted = compute_scores_from_picks(picks_data, {101: 10})
        self.assertEqual(raw, 60)
        self.assertIsNone(chip)
        self.assertEqual(adjusted, 60)

    def test_triple_captain_subtracts_one_multiplier(self):
        picks_data = {
            "entry_history": {"points": 70},
            "active_chip": "3xc",
            "picks": [{"element": 101, "position": 1, "is_captain": True}],
        }
        raw, chip, adjusted = compute_scores_from_picks(picks_data, {101: 10})
        self.assertEqual(raw, 70)
        self.assertEqual(chip, "3xc")
        self.assertEqual(adjusted, 60)  # 70 - 10

    def test_bench_boost_subtracts_bench_sum(self):
        picks_data = {
            "entry_history": {"points": 55},
            "active_chip": "bboost",
            "picks": [
                {"element": 101, "position": 1, "is_captain": True},
                {"element": 104, "position": 12},
                {"element": 105, "position": 13},
            ],
        }
        raw, chip, adjusted = compute_scores_from_picks(picks_data, {101: 10, 104: 2, 105: 1})
        self.assertEqual(raw, 55)
        self.assertEqual(chip, "bboost")
        self.assertEqual(adjusted, 52)  # 55 - (2 + 1)

    def test_wildcard_does_not_change_score(self):
        picks_data = {
            "entry_history": {"points": 45},
            "active_chip": "wildcard",
            "picks": [{"element": 101, "position": 1, "is_captain": True}],
        }
        raw, chip, adjusted = compute_scores_from_picks(picks_data, {101: 10})
        self.assertEqual(adjusted, raw)


class ProcessGameweekTests(TestCase):
    """
    Full pipeline test using mocked FPL API responses.
    """

    def setUp(self):
        self.user1 = User.objects.create_user(username="u1", password="pass", fpl_team_id=342)
        self.user2 = User.objects.create_user(username="u2", password="pass", fpl_team_id=367)
        self.league = League.objects.create(owner=self.user1, name="Test League", start_gameweek=1, total_gameweeks=4)
        self.member1 = LeagueMember.objects.create(league=self.league, user=self.user1)
        self.member2 = LeagueMember.objects.create(league=self.league, user=self.user2)
        self.gw = Gameweek.objects.create(number=1)

    @patch("fpl.processing.fetch_gameweek_live_points")
    @patch("fpl.processing.fetch_gameweek_picks")
    def test_process_gameweek_creates_scores_and_standings(self, mock_picks, mock_live):
        mock_live.return_value = {101: 10, 102: 8}

        def picks_side_effect(team_id, gw_number):
            if team_id == 342:
                return {"entry_history": {"points": 60}, "active_chip": None, "picks": [{"element": 101, "position": 1, "is_captain": True}]}
            return {"entry_history": {"points": 70}, "active_chip": "3xc", "picks": [{"element": 101, "position": 1, "is_captain": True}]}

        mock_picks.side_effect = picks_side_effect

        result = process_gameweek(self.gw)

        self.assertEqual(result["members_processed"], 2)
        self.assertEqual(result["errors"], [])

        ws1 = WeeklyScore.objects.get(league_member=self.member1, gameweek=self.gw)
        ws2 = WeeklyScore.objects.get(league_member=self.member2, gameweek=self.gw)
        self.assertEqual(ws1.adjusted_points, 60)
        self.assertEqual(ws2.adjusted_points, 60)  # 70 - 10 captain bonus

        standings = Standing.objects.filter(gameweek=self.gw)
        self.assertEqual(standings.count(), 2)

        self.gw.refresh_from_db()
        self.assertTrue(self.gw.is_processed)

    @patch("fpl.processing.fetch_gameweek_live_points")
    @patch("fpl.processing.fetch_gameweek_picks")
    def test_missing_fpl_team_id_recorded_as_error(self, mock_picks, mock_live):
        self.user1.fpl_team_id = None
        self.user1.save()
        mock_live.return_value = {}
        mock_picks.return_value = {"entry_history": {"points": 70}, "active_chip": None, "picks": []}

        result = process_gameweek(self.gw)

        self.assertEqual(result["members_processed"], 1)  # only member2 processed
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("u1", result["errors"][0])