from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, AthleteProfile, FanProfile

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('middle_name', 'phone', 'avatar')}),
    )

@admin.register(AthleteProfile)
class AthleteProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'birth_date', 'swimming_level')
    list_filter = ('swimming_level',)
    search_fields = ('user__first_name', 'user__last_name')

@admin.register(FanProfile)
class FanProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__first_name', 'user__last_name')
from .models import Achievement

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('athlete', 'title', 'achievement_type', 'date')
    list_filter = ('achievement_type',)
    search_fields = ('athlete__user__first_name', 'athlete__user__last_name', 'title')
