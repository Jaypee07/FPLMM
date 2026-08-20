from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import CreateView, DetailView

from fpl.models import Standing

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


class LeagueDetailView(LoginRequiredMixin, DetailView):
    model = League
    template_name = "leagues/league_detail.html"
    context_object_name = "league"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        league = self.object

        context["members"] = league.members.select_related("user").all()
        context["is_owner"] = league.owner_id == self.request.user.id
        context["is_member"] = league.members.filter(user=self.request.user).exists()

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