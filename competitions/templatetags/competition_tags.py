from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def is_secretary(context):
    user = context['user']
    return user.is_authenticated and (user.is_staff or hasattr(user, 'secretary_profile'))
