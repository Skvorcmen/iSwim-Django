from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from datetime import date
from .models import Branch, BranchComment
from competitions.models import Competition, Registration
from trainers.models import Trainer
from users.models import AthleteProfile

class BranchListView(ListView):
    model = Branch
    template_name = 'branches/branch_list.html'
    context_object_name = 'branches'

class BranchDetailView(DetailView):
    model = Branch
    template_name = 'branches/branch_detail.html'
    context_object_name = 'branch'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comments'] = self.object.comments.all().order_by('-created_at')
        ctx['total_comments'] = ctx['comments'].count()
        return ctx

class BranchCabinetView(LoginRequiredMixin, TemplateView):
    template_name = 'branches/branch_cabinet.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        branch_id = self.kwargs.get('pk')
        branch = Branch.objects.get(pk=branch_id)
        ctx['branch'] = branch
        competitions = Competition.objects.filter(branch=branch).order_by('-start_date')
        ctx['competitions_count'] = competitions.count()
        ctx['upcoming_competitions'] = competitions.filter(start_date__gte=date.today())[:5]
        registrations = Registration.objects.filter(branch=branch)
        ctx['athletes'] = AthleteProfile.objects.filter(
            registration__branch=branch
        ).distinct()
        ctx['athletes_count'] = ctx['athletes'].count()
        ctx['trainers'] = Trainer.objects.filter(branches=branch).distinct()
        ctx['trainers_count'] = ctx['trainers'].count()
        return ctx

@login_required
def add_comment_ajax(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            comment = BranchComment.objects.create(branch=branch, user=request.user, text=text)
            return JsonResponse({
                'success': True,
                'user': request.user.get_full_name() or request.user.email,
                'text': comment.text,
                'date': comment.created_at.strftime('%d.%m.%Y %H:%M'),
                'total': branch.comments.count()
            })
    return JsonResponse({'success': False})
