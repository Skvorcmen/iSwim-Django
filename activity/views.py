from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Activity

class ActivityListView(ListView):
    model = Activity
    template_name = 'activity/activity_list.html'
    context_object_name = 'activities'
    paginate_by = 20

    def get_queryset(self):
        queryset = Activity.objects.select_related('user')
        activity_type = self.request.GET.get('type')
        if activity_type in dict(Activity.ACTIVITY_TYPES):
            queryset = queryset.filter(activity_type=activity_type)
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['activity_types'] = Activity.ACTIVITY_TYPES
        ctx['selected_type'] = self.request.GET.get('type', '')
        ctx['page_title'] = 'Лента активности'
        return ctx

class PersonalActivityListView(LoginRequiredMixin, ActivityListView):
    def get_queryset(self):
        queryset = super().get_queryset().filter(user=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Моя лента активности'
        return ctx
