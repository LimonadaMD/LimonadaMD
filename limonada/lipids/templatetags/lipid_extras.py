from django import template
from lipids.views import LM_class


register = template.Library()


@register.simple_tag()
def lm_select(val):
    lmclass, lmdict = LM_class()
    options = []
    if val in lmclass.keys():
       options = lmclass[val] 
    elif val == "all":
       options = lmclass 
    return options


