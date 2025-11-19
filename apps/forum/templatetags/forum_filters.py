from django import template
from django.utils.safestring import mark_safe
from ..utils import render_forum_content

register = template.Library()

@register.filter(name='forum_content')
def forum_content(value):
    """Фильтр для обработки контента форума"""
    return mark_safe(render_forum_content(value))

@register.filter(name='truncate_html')
def truncate_html(value, length=200):
    """Обрезание HTML контента"""
    if len(value) > length:
        return value[:length] + '...'
    return value
