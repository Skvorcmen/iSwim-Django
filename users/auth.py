from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.models import Group


# ==================== ROLE DETECTION ====================

def get_user_role(user):
    """
    Определяет роль пользователя.
    Сначала проверяет Django Groups (новый способ), потом profile (legacy).
    Возвращает: 'admin', 'secretary', 'trainer', 'athlete', 'fan' или None
    """
    if not user.is_authenticated:
        return None
    
    if user.is_superuser:
        return 'admin'
    
    # Проверяем Django Groups (новый стандартный способ)
    groups = user.groups.values_list('name', flat=True)
    
    if 'Admin' in groups:
        return 'admin'
    if 'Secretary' in groups:
        return 'secretary'
    if 'Trainer' in groups:
        return 'trainer'
    if 'Athlete' in groups:
        return 'athlete'
    if 'Fan' in groups:
        return 'fan'
    if user.is_staff:
        return 'secretary'
    
    # Fallback на profile (legacy support)
    if getattr(user, 'secretary_profile', None):
        return 'secretary'
    if getattr(user, 'trainer_profile', None):
        return 'trainer'
    if getattr(user, 'athlete_profile', None):
        return 'athlete'
    if getattr(user, 'fan_profile', None):
        return 'fan'
    
    return None


def assign_user_to_role(user, role):
    """
    Добавляет пользователя в соответствующую Django Group.
    role: 'admin', 'secretary', 'trainer', 'athlete', 'fan'
    """
    role_to_group = {
        'admin': 'Admin',
        'secretary': 'Secretary',
        'trainer': 'Trainer',
        'athlete': 'Athlete',
        'fan': 'Fan',
    }
    
    group_name = role_to_group.get(role)
    if not group_name:
        return False
    
    try:
        group = Group.objects.get(name=group_name)
        user.groups.add(group)
        return True
    except Group.DoesNotExist:
        return False


def remove_user_from_role(user, role):
    """Удаляет пользователя из группы."""
    role_to_group = {
        'admin': 'Admin',
        'secretary': 'Secretary',
        'trainer': 'Trainer',
        'athlete': 'Athlete',
        'fan': 'Fan',
    }
    
    group_name = role_to_group.get(role)
    if not group_name:
        return False
    
    try:
        group = Group.objects.get(name=group_name)
        user.groups.remove(group)
        return True
    except Group.DoesNotExist:
        return False


def has_role(user, *roles):
    """Проверяет, есть ли у пользователя одна из указанных ролей"""
    user_role = get_user_role(user)
    return user_role in roles


def permission_required(permission_codename):
    """
    Декоратор для проверки Django permission.

    Использование:
        @permission_required('competitions.change_competition')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if request.user.has_perm(permission_codename):
                return view_func(request, *args, **kwargs)
            messages.error(request, 'У вас нет прав доступа к этому разделу')
            return redirect('home')
        return wrapped_view
    return decorator


# ==================== DECORATORS ====================

def role_required(*required_roles):
    """
    Декоратор для проверки ролей пользователя.
    
    Использование:
        @role_required('secretary', 'admin')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if has_role(request.user, *required_roles):
                return view_func(request, *args, **kwargs)
            messages.error(request, 'У вас нет прав доступа к этому разделу')
            return redirect('home')
        return wrapped_view
    return decorator


# Shortcuts для конкретных ролей
def admin_required(view_func):
    return role_required('admin')(view_func)


def secretary_required(view_func):
    return role_required('secretary', 'admin')(view_func)


def trainer_required(view_func):
    return role_required('trainer', 'admin')(view_func)


def athlete_required(view_func):
    return role_required('athlete')(view_func)


# ==================== MIXINS ====================

class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Миксин для class-based views, проверяющий роль пользователя.
    
    Использование:
        class MyView(RoleRequiredMixin, DetailView):
            required_roles = ['secretary', 'admin']
    """
    required_roles = []
    permission_denied_message = 'У вас нет прав доступа к этому разделу'
    
    def test_func(self):
        if not self.required_roles:
            return True
        return has_role(self.request.user, *self.required_roles)
    
    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect('home')


class AdminRequiredMixin(RoleRequiredMixin):
    """Миксин для администраторов"""
    required_roles = ['admin']
    permission_denied_message = 'Доступ только для администраторов'


class SecretaryRequiredMixin(RoleRequiredMixin):
    """Миксин для секретарей и администраторов"""
    required_roles = ['secretary', 'admin']
    permission_denied_message = 'Доступ только для секретарей и администраторов'


class TrainerRequiredMixin(RoleRequiredMixin):
    """Миксин для тренеров и администраторов"""
    required_roles = ['trainer', 'admin']
    permission_denied_message = 'Доступ только для тренеров'


class AthleteRequiredMixin(RoleRequiredMixin):
    """Миксин для спортсменов"""
    required_roles = ['athlete']
    permission_denied_message = 'Доступ только для спортсменов'


# ==================== MIDDLEWARE ====================

class RoleMiddleware:
    """
    Middleware для добавления информации о роли в request object.
    
    После обработки middleware, request.user_role будет содержать:
    'admin', 'secretary', 'trainer', 'athlete', 'fan' или None
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        request.user_role = get_user_role(request.user) if request.user.is_authenticated else None
        response = self.get_response(request)
        return response
