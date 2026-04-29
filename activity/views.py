from django.views.generic import ListView
from .models import Activity

class ActivityListView(ListView):
    model = Activity
    template_name = 'activity/activity_list.html'
    context_object_name = 'activities'
    paginate_by = 20
