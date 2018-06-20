from django import template


register = template.Library()


@register.assignment_tag
def lipidnames(qs):
    lipids = []
    for comp in qs:
       l = comp.topology.lipid #.name
       if l not in lipids:
           lipids.append(l)
    
    return lipids

