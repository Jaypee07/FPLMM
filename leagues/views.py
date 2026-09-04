from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import CreateView, DetailView

from fpl.models import Standing, WeeklyScore

from .forms import JoinLeagueForm, LeagueCreateForm
from .models import League, LeagueMember


class CreateLeagueView(LoginRequiredMixin, CreateView):
    form_class = LeagueCreateForm
    template_name = "leagues/create_league.html"

    def form_valid(self, form):
        with transaction.atomic():
            league = form.save(commit=False)
            league.owner = self.request.user
            league.save()

            LeagueMember.objects.create(
                league=league,
                user=self.request.user,
            )

        self.object = league
        messages.success(self.request, f"League '{league.name}' created. Invite code: {league.code}")
        return redirect("league-detail", pk=league.pk)


class JoinLeagueView(LoginRequiredMixin, View):
    template_name = "leagues/join_league.html"

    def get(self, request):
        form = JoinLeagueForm()
        return self._render(request, form)

    def post(self, request):
        form = JoinLeagueForm(request.POST)

        if not form.is_valid():
            return self._render(request, form)

        code = form.cleaned_data["code"]
        league = League.objects.filter(code=code, is_active=True).first()

        if not league:
            form.add_error("code", "No active league found with this invite code.")
            return self._render(request, form)

        if LeagueMember.objects.filter(league=league, user=request.user).exists():
            messages.info(request, f"You're already a member of '{league.name}'.")
            return redirect("league-detail", pk=league.pk)

        LeagueMember.objects.create(league=league, user=request.user)
        messages.success(request, f"You've joined '{league.name}'.")
        return redirect("league-detail", pk=league.pk)

    def _render(self, request, form):
        return render(request, self.template_name, {"form": form})


class LeagueMembershipRequiredMixin:
    """
    Ensures the requesting user is a member of the League being viewed,
    not just logged in. Raises 403 (PermissionDenied) otherwise, which
    Django renders as a clean "Forbidden" page rather than leaking data.
    """

    def _get_league(self):
        raise NotImplementedError

    def dispatch(self, request, *args, **kwargs):
        league = self._get_league()
        if not LeagueMember.objects.filter(league=league, user=request.user).exists():
            raise PermissionDenied("You are not a member of this league.")
        return super().dispatch(request, *args, **kwargs)


class LeagueDetailView(LoginRequiredMixin, LeagueMembershipRequiredMixin, DetailView):
    model = League
    template_name = "leagues/league_detail.html"
    context_object_name = "league"

    def _get_league(self):
        return League.objects.filter(pk=self.kwargs["pk"]).first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        league = self.object

        context["members"] = league.members.select_related("user").all()
        context["is_owner"] = league.owner_id == self.request.user.id
        context["is_member"] = True  # guaranteed by LeagueMembershipRequiredMixin

        latest_standings = (
            Standing.objects.filter(league_member__league=league)
            .select_related("league_member__user", "gameweek")
            .order_by("-gameweek__number")
        )

        latest_gameweek_number = latest_standings.first().gameweek.number if latest_standings.exists() else None

        if latest_gameweek_number:
            context["leaderboard"] = latest_standings.filter(
                gameweek__number=latest_gameweek_number
            ).order_by("rank")
            context["leaderboard_gameweek"] = latest_gameweek_number
        else:
            context["leaderboard"] = None
            context["leaderboard_gameweek"] = None

        return context


class MemberPerformanceView(LoginRequiredMixin, LeagueMembershipRequiredMixin, DetailView):
    model = LeagueMember
    template_name = "leagues/member_performance.html"
    context_object_name = "member"
    pk_url_kwarg = "member_pk"

    def _get_league(self):
        return League.objects.filter(pk=self.kwargs["league_pk"]).first()

    def get_queryset(self):
        return LeagueMember.objects.filter(league_id=self.kwargs["league_pk"]).select_related("user", "league")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = self.object
        league = member.league

        weekly_scores = WeeklyScore.objects.filter(
            league_member=member
        ).select_related("gameweek").order_by("gameweek__number")

        standings = {
            s.gameweek_id: s
            for s in Standing.objects.filter(league_member=member).select_related("gameweek")
        }

        history = []
        for ws in weekly_scores:
            standing = standings.get(ws.gameweek_id)
            history.append({
                "gameweek": ws.gameweek.number,
                "raw_points": ws.raw_points,
                "chip_used": ws.chip_used,
                "adjusted_points": ws.adjusted_points,
                "points_used": ws.score_for_standing,
                "cumulative_points": standing.total_points if standing else None,
                "rank": standing.rank if standing else None,
            })

        context["history"] = history
        context["league"] = league
        return context