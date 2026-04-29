from django.contrib import admin
from .models import Competition, Registration, Result, BranchScore

@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'status', 'registered_count', 'location')
    list_filter = ('status', 'branch')
    search_fields = ('title', 'location')

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('competition', 'athlete', 'created_at', 'is_confirmed')
    list_filter = ('is_confirmed', 'competition')

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('competition', 'athlete', 'discipline', 'place', 'result_time')
    list_filter = ('competition', 'discipline')

@admin.register(BranchScore)
class BranchScoreAdmin(admin.ModelAdmin):
    list_display = ('competition', 'branch', 'total_points', 'gold', 'silver', 'bronze')
