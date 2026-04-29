from django.contrib import admin
from .models import Activity

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'activity_type', 'user', 'created_at')
    list_filter = ('activity_type',)
    search_fields = ('title',)
