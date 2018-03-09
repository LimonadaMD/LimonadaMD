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


@register.filter(name='substring')
def substring(value,args):
    if args is not None:
        arg_list = [arg.strip() for arg in args.split(',')]
        start = 0
        end = 20
        try:
           start = int(arg_list[0])
        except:
           pass
        if len(arg_list) == 2:
            try:
               end = int(arg_list[1])
            except:
               pass
        value = value[start:end]
    return value



