from django import template
from .. import __version__
import urllib, os


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


@register.assignment_tag
def queryorder(qs, param, direction):
    """ template tag which allows queryset ordering. Usage:
          {% query books "author" "asc" as mybooks %}
          {% for book in mybooks %}
            ...
          {% endfor %}
    """
    if direction == "asc":
        return qs.order_by(param)
    else:
        return qs.order_by(param).reverse()


@register.filter(name='basename')
def split(value):
    return str(value).split("/")[-1]  


@register.filter(name='dirname')
def dirname(value):
    return os.path.dirname(value)   








