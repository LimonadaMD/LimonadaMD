# -*- coding: utf-8; Mode: python; tab-width: 4; indent-tabs-mode:nil; -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
#    Limonada is accessible at https://limonada.univ-reims.fr/
#    Copyright (C) 2016-2020 - The Limonada Team (see the AUTHORS file)
#
#    This file is part of Limonada.
#
#    Limonada is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Limonada is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Limonada.  If not, see <http://www.gnu.org/licenses/>.

# standard library
import operator
from functools import reduce

# Django
from django import template
from django.db.models import Q

# local Django
from forcefields.models import Forcefield, Software

register = template.Library()


@register.simple_tag()
def sv_select(val):
    """ This function finds the different versions of a software in order to fill
        dropdown select version on page load.
    """
    options = list(("", "-----"))
    if val != "":
        softlist = Software.objects.filter(abbreviation__istartswith=val).order_by('order')
        if softlist:
            options = list((obj.id, obj.version) for obj in softlist)
    return options


@register.simple_tag()
def ff_select(software, softversion):
    """ This function finds the forcefields that can be used with one or several
        softwares in order to fill dropdown select field on page load.
    """
    if type(softversion) is list:
        softlist = softversion
    elif type(softversion) is int:
        softlist = [softversion]
    elif software != "" and not softversion:
        softlist = Software.objects.filter(abbreviation__istartswith=software).values_list('id', flat=True)
    else:
        softlist = softversion.split(',')
    options = list(("", "-----"))
    if softlist:
        querylist = []
        for i in softlist:
            querylist.append(Q(software=Software.objects.filter(id=i)[0]))
        ff_list = Forcefield.objects.all()
        ff_list = ff_list.filter(reduce(operator.or_, querylist)).distinct()
        options = list((obj.id, obj.name) for obj in ff_list)
    return options
