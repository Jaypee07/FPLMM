from django.urls import path

from . import views

urlpatterns = [
    path("fixtures/", views.FixturesView.as_view(), name="fixtures"),
    path("results/", views.ResultsView.as_view(), name="results"),
]