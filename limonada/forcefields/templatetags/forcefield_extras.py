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

# Django
from django import template

# local Django
from forcefields.choices import SFTYPE_CHOICES
from forcefields.models import Forcefield

register = template.Library()


@register.simple_tag()
def ff_select(val):
    if val == 'all':
        options = {}
        for ff in SFTYPE_CHOICES:
            options[ff[0]] = [[obj.id, str(obj.name)] for obj in Forcefield.objects.filter(software=ff[0])]
    else:
        options = list((obj.id, obj.name) for obj in Forcefield.objects.filter(software=val))
    return options
