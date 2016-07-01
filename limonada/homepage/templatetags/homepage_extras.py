from django import template
from .. import __version__

register = template.Library()

@register.simple_tag
def version():
    return __version__