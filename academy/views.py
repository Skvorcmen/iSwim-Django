from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import Article, ArticleComment, ArticleLike

class ArticleListView(ListView):
    model = Article
    template_name = 'academy/article_list.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        queryset = Article.objects.all()
        
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )
        
        category = self.request.GET.get('category', '')
        if category:
            queryset = queryset.filter(category=category)
        
        sort = self.request.GET.get('sort', 'newest')
        if sort == 'oldest':
            queryset = queryset.order_by('published_at')
        elif sort == 'popular':
            queryset = sorted(queryset, key=lambda a: a.likes.count(), reverse=True)
        else:
            queryset = queryset.order_by('-published_at')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_search'] = self.request.GET.get('search', '')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        context['categories'] = Article.CATEGORY_CHOICES
        return context

class ArticleDetailView(DetailView):
    model = Article
    template_name = 'academy/article_detail.html'
    context_object_name = 'article'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all()
        if self.request.user.is_authenticated:
            context['user_liked'] = self.object.likes.filter(user=self.request.user).exists()
        return context

@login_required
def toggle_like(request, slug):
    article = get_object_or_404(Article, slug=slug)
    like, created = ArticleLike.objects.get_or_create(article=article, user=request.user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({'liked': liked, 'count': article.likes.count()})

@login_required
def add_comment_ajax(request, slug):
    article = get_object_or_404(Article, slug=slug)
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            comment = ArticleComment.objects.create(article=article, user=request.user, text=text)
            return JsonResponse({
                'success': True,
                'user': request.user.get_full_name() or request.user.email,
                'text': comment.text,
                'date': comment.created_at.strftime('%d.%m.%Y %H:%M'),
                'total': article.comments.count()
            })
    return JsonResponse({'success': False})
