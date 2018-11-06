# -*- coding: utf-8; Mode: python; tab-width: 4; indent-tabs-mode:nil; -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
#    Limonada is accessible at https://www.limonadamd.eu/
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

# Django
from django import template
from django.db.models import Q

# local Django
from forcefields.choices import SFTYPE_CHOICES
from forcefields.models import Forcefield, Software

register = template.Library()


@register.simple_tag()
def ff_select(val):
    if type(val) is list:
        softlist = val
    elif type(val) is int:
        softlist = [val]
    else:
        softlist = val.split(',')
    querylist = []
    for i in softlist:
        querylist.append(Q(software=Software.objects.filter(id=i)))
    ff_list = Forcefield.objects.all() 
    ff_list = ff_list.filter(reduce(operator.or_, querylist))
    options = list((obj.id, obj.name) for obj in ff_list)
    return options
