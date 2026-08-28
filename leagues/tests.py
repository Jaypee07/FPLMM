from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError

from accounts.models import User
from leagues.models import League, LeagueMember


class LeagueModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass", fpl_team_id=1)

    def test_league_cannot_extend_beyond_gw38(self):
        league = League(owner=self.owner, name="Too Long", start_gameweek=35, total_gameweeks=10)
        with self.assertRaises(ValidationError):
            league.save()

    def test_end_gameweek_calculated_correctly(self):
        league = League.objects.create(owner=self.owner, name="Valid", start_gameweek=5, total_gameweeks=10)
        self.assertEqual(league.end_gameweek, 14)

    def test_invite_code_generated_and_unique(self):
        league1 = League.objects.create(owner=self.owner, name="L1", start_gameweek=1, total_gameweeks=4)
        league2 = League.objects.create(owner=self.owner, name="L2", start_gameweek=1, total_gameweeks=4)
        self.assertNotEqual(league1.code, league2.code)
        self.assertEqual(len(league1.code), 6)


class LeagueMemberModelTests(TestCase):
    def test_duplicate_membership_rejected(self):
        owner = User.objects.create_user(username="owner", password="pass", fpl_team_id=1)
        league = League.objects.create(owner=owner, name="L1", start_gameweek=1, total_gameweeks=4)
        LeagueMember.objects.create(league=league, user=owner)

        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            LeagueMember.objects.create(league=league, user=owner)


class CreateLeagueViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="creator", password="pass", fpl_team_id=1)
        self.client.login(username="creator", password="pass")

    def test_owner_becomes_member_on_creation(self):
        response = self.client.post(reverse("create-league"), {
            "name": "My League",
            "start_gameweek": 1,
            "total_gameweeks": 4,
            "include_chip_points": False,
        })
        league = League.objects.get(name="My League")
        self.assertEqual(league.owner, self.user)
        self.assertTrue(LeagueMember.objects.filter(league=league, user=self.user).exists())
        self.assertEqual(league.members.count(), 1)

    def test_chip_points_forced_off_for_short_leagues(self):
        self.client.post(reverse("create-league"), {
            "name": "Short League",
            "start_gameweek": 1,
            "total_gameweeks": 5,
            "include_chip_points": True,  # attempting to bypass client-side disable
        })
        league = League.objects.get(name="Short League")
        self.assertFalse(league.include_chip_points)


class JoinLeagueViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass", fpl_team_id=1)
        self.joiner = User.objects.create_user(username="joiner", password="pass", fpl_team_id=2)
        self.league = League.objects.create(owner=self.owner, name="Joinable", start_gameweek=1, total_gameweeks=4)
        LeagueMember.objects.create(league=self.league, user=self.owner)

    def test_valid_code_joins_league(self):
        self.client.login(username="joiner", password="pass")
        response = self.client.post(reverse("join-league"), {"code": self.league.code})
        self.assertTrue(LeagueMember.objects.filter(league=self.league, user=self.joiner).exists())

    def test_invalid_code_rejected(self):
        self.client.login(username="joiner", password="pass")
        response = self.client.post(reverse("join-league"), {"code": "ZZZZZZ"})
        self.assertFalse(LeagueMember.objects.filter(league=self.league, user=self.joiner).exists())
        self.assertContains(response, "No active league found")

    def test_duplicate_join_does_not_error(self):
        LeagueMember.objects.create(league=self.league, user=self.joiner)
        self.client.login(username="joiner", password="pass")
        response = self.client.post(reverse("join-league"), {"code": self.league.code}, follow=True)
        self.assertEqual(LeagueMember.objects.filter(league=self.league, user=self.joiner).count(), 1)


class LeagueMembershipPermissionTests(TestCase):
    """
    Confirms the fix: non-members cannot view a league's detail or a
    member's performance page just by guessing the URL.
    """

    def setUp(self):
        self.member_user = User.objects.create_user(username="member", password="pass", fpl_team_id=1)
        self.outsider = User.objects.create_user(username="outsider", password="pass", fpl_team_id=2)
        self.league = League.objects.create(owner=self.member_user, name="Private League", start_gameweek=1, total_gameweeks=4)
        self.member = LeagueMember.objects.create(league=self.league, user=self.member_user)

    def test_member_can_view_league_detail(self):
        self.client.login(username="member", password="pass")
        response = self.client.get(reverse("league-detail", kwargs={"pk": self.league.pk}))
        self.assertEqual(response.status_code, 200)

    def test_non_member_forbidden_from_league_detail(self):
        self.client.login(username="outsider", password="pass")
        response = self.client.get(reverse("league-detail", kwargs={"pk": self.league.pk}))
        self.assertEqual(response.status_code, 403)

    def test_non_member_forbidden_from_member_performance(self):
        self.client.login(username="outsider", password="pass")
        response = self.client.get(reverse("member-performance", kwargs={"league_pk": self.league.pk, "member_pk": self.member.pk}))
        self.assertEqual(response.status_code, 403)