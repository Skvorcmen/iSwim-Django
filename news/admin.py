from django.contrib import admin
from .models import News, NewsComment, NewsLike

class NewsCommentInline(admin.TabularInline):
    model = NewsComment
    extra = 0

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_at', 'is_published', 'likes_count', 'comments_count')
    list_filter = ('is_published',)
    search_fields = ('title', 'short_text')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [NewsCommentInline]

    def likes_count(self, obj):
        return obj.likes.count()
    likes_count.short_description = 'Лайки'

    def comments_count(self, obj):
        return obj.comments.count()
    comments_count.short_description = 'Комментарии'

@admin.register(NewsComment)
class NewsCommentAdmin(admin.ModelAdmin):
    list_display = ('news', 'user', 'created_at')

@admin.register(NewsLike)
class NewsLikeAdmin(admin.ModelAdmin):
    list_display = ('news', 'user', 'created_at')
