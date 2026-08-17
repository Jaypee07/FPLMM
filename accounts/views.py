from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.generic import CreateView, FormView

from fpl.services import fetch_fpl_entry

from .forms import RegistrationForm, ResendVerificationForm
from .models import User
from .tokens import email_verification_token


def _send_verification_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    verify_url = request.build_absolute_uri(
        reverse("verify-email", kwargs={"uidb64": uid, "token": token})
    )

    send_mail(
        subject="Verify your FPLMM account",
        message=(
            f"Hi {user.username},\n\n"
            f"Click the link below to verify your account:\n{verify_url}\n\n"
            "This link expires in 3 days. If you don't see this email, check your "
            "Spam/Junk folder — mark it as 'Not spam' so future FPLMM emails reach "
            "your inbox directly.\n\n"
            "If you didn't sign up for FPLMM, ignore this email."
        ),
        from_email=None,
        recipient_list=[user.email],
    )


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = "/accounts/registration-pending/"

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        _send_verification_email(self.request, user)

        return super().form_valid(form)


class VerifyEmailView(View):
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = get_object_or_404(User, pk=uid)
        except (TypeError, ValueError, OverflowError):
            return redirect("registration-invalid")

        if user.is_active:
            # Already verified — link was clicked twice, or reused. Not an error.
            return redirect("login")

        if email_verification_token.check_token(user, token):
            user.is_active = True
            user.save()
            return redirect("login")

        return redirect("registration-invalid")


class ResendVerificationView(FormView):
    form_class = ResendVerificationForm
    template_name = "accounts/resend_verification.html"
    success_url = "/accounts/registration-pending/"

    def form_valid(self, form):
        _send_verification_email(self.request, form.user)
        return super().form_valid(form)


def registration_pending(request):
    return render(request, "accounts/registration_pending.html")


def registration_invalid(request):
    return render(request, "accounts/registration_invalid.html")


def validate_fpl_id(request):
    team_id = request.GET.get("fpl_team_id", "").strip()

    if not team_id.isdigit():
        return JsonResponse({"valid": False})

    entry = fetch_fpl_entry(team_id)
    if entry:
        return JsonResponse({
            "valid": True,
            "name": entry["name"],
            "team_name": entry["team_name"],
        })

    return JsonResponse({"valid": False})


class FPLMMLoginView(auth_views.LoginView):
    """
    Custom login view that gives a clear, specific message when the
    account exists but hasn't been verified yet, instead of Django's
    generic 'invalid credentials' message which hides the real cause.
    """
    template_name = "accounts/login.html"

    def form_invalid(self, form):
        username = form.data.get("username")
        user = User.objects.filter(username=username).first()

        if user and not user.is_active:
            form.add_error(
                None,
                "This account exists but hasn't been verified yet. "
                "Check your email, or use the resend verification option below."
            )
            return self.render_to_response(self.get_context_data(form=form))

        return super().form_invalid(form)