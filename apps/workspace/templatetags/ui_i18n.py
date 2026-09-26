from django import template
from django.utils.translation import gettext

register = template.Library()

@register.filter
def translate_ui(value):
    """Translate stored system labels without altering user-entered names."""
    if value is None:
        return value
    return gettext(str(value))
