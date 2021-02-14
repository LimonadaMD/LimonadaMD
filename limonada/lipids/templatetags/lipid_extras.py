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

# Django
from django import template

# local Django
from lipids.models import Topology
from lipids.views import lm_class

register = template.Library()


@register.simple_tag()
def lm_select(val):
    """ This function finds the child elements of a LipidMaps class
        in order to fill a dropdown select field on page load.
    """
    lmclass, lmdict = lm_class()
    options = []
    if val in lmclass.keys():
        options = lmclass[val]
    return options


@register.simple_tag()
def top_select(lipid, forcefield):
    """ This function finds the topologies available for a particular lipid and
        forcefield in order to fill dropdown select field on page load.
    """
    top_list = Topology.objects.filter(lipid__id=lipid)
    top_list = top_list.filter(forcefield__id=forcefield)
    options = list((obj.id, obj.version) for obj in top_list)
    return options


@register.filter(name='substring')
def substring(value, args):
    if args is not None:
        arg_list = [arg.strip() for arg in args.split(',')]
        start = 0
        end = -1
        try:
            start = int(arg_list[0])
        except ValueError:
            start = 0
        if len(arg_list) == 2:
            try:
                end = int(arg_list[1])
            except ValueError:
                end = -1
        value = value[start:end]
    return value
