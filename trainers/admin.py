from django.contrib import admin
from .models import Trainer

@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'experience_years', 'is_active')
    list_filter = ('is_active', 'branches')
    search_fields = ('user__first_name', 'user__last_name', 'specialization', 'certifications')
