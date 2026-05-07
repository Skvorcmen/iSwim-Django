from django import template
from users.auth import has_role

register = template.Library()

@register.simple_tag(takes_context=True)
def is_secretary(context):
    user = context['user']
    return user.is_authenticated and has_role(user, 'secretary', 'admin')
