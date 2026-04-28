from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import News, NewsComment, NewsLike

class NewsListView(ListView):
    model = News
    template_name = 'news/news_list.html'
    context_object_name = 'news_list'
    paginate_by = 10

    def get_queryset(self):
        queryset = News.objects.filter(is_published=True)
        
        # Поиск
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(short_text__icontains=search) | 
                Q(full_text__icontains=search)
            )
        
        # Фильтр по году и месяцу
        year = self.request.GET.get('year', '')
        month = self.request.GET.get('month', '')
        if year:
            queryset = queryset.filter(published_at__year=year)
        if month:
            queryset = queryset.filter(published_at__month=month)
        
        # Сортировка
        sort = self.request.GET.get('sort', 'newest')
        if sort == 'oldest':
            queryset = queryset.order_by('published_at')
        elif sort == 'popular':
            queryset = sorted(queryset, key=lambda n: n.likes.count(), reverse=True)
        else:
            queryset = queryset.order_by('-published_at')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Годы для фильтра
        years = News.objects.filter(is_published=True).dates('published_at', 'year')
        context['years'] = list(set(d.year for d in years))
        context['years'].sort(reverse=True)
        # Текущие фильтры
        context['current_search'] = self.request.GET.get('search', '')
        context['current_year'] = self.request.GET.get('year', '')
        context['current_month'] = self.request.GET.get('month', '')
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        return context

class NewsDetailView(DetailView):
    model = News
    template_name = 'news/news_detail.html'
    context_object_name = 'news'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all()
        if self.request.user.is_authenticated:
            context['user_liked'] = self.object.likes.filter(user=self.request.user).exists()
        return context

@login_required
def toggle_like(request, slug):
    news = get_object_or_404(News, slug=slug)
    like, created = NewsLike.objects.get_or_create(news=news, user=request.user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({'liked': liked, 'count': news.likes.count()})

@login_required
def add_comment_ajax(request, slug):
    news = get_object_or_404(News, slug=slug)
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            comment = NewsComment.objects.create(news=news, user=request.user, text=text)
            return JsonResponse({
                'success': True,
                'user': request.user.get_full_name() or request.user.email,
                'text': comment.text,
                'date': comment.created_at.strftime('%d.%m.%Y %H:%M'),
                'total': news.comments.count()
            })
    return JsonResponse({'success': False})
