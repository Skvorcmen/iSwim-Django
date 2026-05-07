from django.contrib import admin
from .models import Branch, BranchComment

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'address')

@admin.register(BranchComment)
class BranchCommentAdmin(admin.ModelAdmin):
    list_display = ('branch', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'branch__name', 'text')
