from django import template
from forcefields.models import Forcefield
from forcefields.choices import *

register = template.Library()


@register.simple_tag()
def ff_select(val):
    if val == "all":
        options = {}
        for ff in SFTYPE_CHOICES:
           options[ff[0]] = [[obj.id,str(obj.name)] for obj in Forcefield.objects.filter(software=ff[0])]
    else:
        options = list((obj.id,obj.name) for obj in Forcefield.objects.filter(software=val))
    return options

