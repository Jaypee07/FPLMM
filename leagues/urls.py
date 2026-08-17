from django.urls import path

from . import views

urlpatterns = [
    path("create/", views.CreateLeagueView.as_view(), name="create-league"),
    path("join/", views.JoinLeagueView.as_view(), name="join-league"),
    path("<int:pk>/", views.LeagueDetailView.as_view(), name="league-detail"),
]