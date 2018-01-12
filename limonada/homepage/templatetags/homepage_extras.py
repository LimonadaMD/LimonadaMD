from django import template
#from urllib.parse import urlencode
from .. import __version__
import urllib


register = template.Library()


@register.simple_tag
def version():
    return __version__


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context['request'].GET.dict()
    query.update(kwargs)
    return urllib.urlencode(query)


@register.assignment_tag
def query(qs, **kwargs):
    """ template tag which allows queryset filtering. Usage:
          {% query books author=author as mybooks %}
          {% for book in mybooks %}
            ...
          {% endfor %}
    """
    return qs.filter(**kwargs).distinct()


