from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("registration-pending/", views.registration_pending, name="registration-pending"),
    path("registration-invalid/", views.registration_invalid, name="registration-invalid"),
    path("resend-verification/", views.ResendVerificationView.as_view(), name="resend-verification"),
    path("verify-email/<uidb64>/<token>/", views.VerifyEmailView.as_view(), name="verify-email"),
    path("validate-fpl-id/", views.validate_fpl_id, name="validate-fpl-id"),

    path("login/", views.FPLMMLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]