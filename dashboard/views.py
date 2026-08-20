from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from leagues.models import League


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["leagues"] = (
            League.objects.filter(members__user=self.request.user, is_active=True)
            .distinct()
            .order_by("-created_at")
        )
        return context