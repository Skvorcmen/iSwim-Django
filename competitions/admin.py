from django.contrib import admin
from .models import Competition, AgeCategory, Discipline, Registration, Heat, HeatAssignment

class AgeCategoryInline(admin.TabularInline):
    model = AgeCategory
    extra = 1

class DisciplineInline(admin.TabularInline):
    model = Discipline
    extra = 1

@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'status', 'location')
    list_filter = ('status',)
    inlines = [AgeCategoryInline, DisciplineInline]
    search_fields = ('title',)

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('athlete', 'discipline', 'competition', 'preliminary_time', 'is_confirmed')
    list_filter = ('competition', 'discipline')

@admin.register(Heat)
class HeatAdmin(admin.ModelAdmin):
    list_display = ('id', 'competition', 'discipline', 'age_category', 'number')

@admin.register(HeatAssignment)
class HeatAssignmentAdmin(admin.ModelAdmin):
    list_display = ('heat', 'registration', 'lane', 'result_time', 'place')
